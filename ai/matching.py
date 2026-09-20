"""Semantic matching engine with weighted scoring."""

from __future__ import annotations

import math
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Optional

IMAGE_WEIGHT = 0.70
TEXT_WEIGHT = 0.20
METADATA_WEIGHT = 0.10
DEFAULT_MATCH_THRESHOLD = 0.40

# Raw cosine similarity from these encoders is not a 0-1 "how similar are
# these" scale: contrastive embeddings pack into a narrow cone of the
# hypersphere, so even unrelated inputs land at a fairly high baseline and
# near-duplicates only edge a bit higher. FLOOR/CEILING below stretch the
# band where the actual discrimination happens back out to 0-1, so genuinely
# similar (but not pixel-identical) images can clear the match threshold
# instead of only exact duplicates doing so.
#
# IMAGE_SIM_FLOOR/CEILING were measured, not guessed: ran openai/clip-vit-
# base-patch32 (the model this module loads) on real photos (pulled from
# Wikimedia Commons, not staged studio shots) through this exact code path.
# The absolute similarity band shifts a lot with photographic style - clean
# product-style renders separate cleanly (unrelated ~0.68-0.79, same
# physical item ~0.95-1.00), but real "in the wild" photos (different
# angles, a person in frame, different eras/lighting) compress hard: two
# real unrelated items landed at 0.39-0.49, while two photos of the very
# same backpack model - one a candid modern shot, one an archival B&W photo
# - landed at 0.588... which tied EXACTLY with an unrelated item (backpack
# vs. a bicycle, also 0.588). That is a genuine ceiling on what raw
# whole-image cosine similarity can discriminate once photo style varies
# enough, not a threshold that can be tuned away - no floor/ceiling here
# will perfectly separate every case. What this rescaling can still do
# reliably: crush clearly-unrelated pairs to ~0, give a small-but-nonzero
# lift to ambiguous same-category cases (appropriate, since the evidence
# for those is genuinely weak), and let true near-duplicates still read as
# a near-certain match. It is deliberately a soft signal in the 0.70 image
# weight below, not a hard filter - text description and metadata (and,
# ultimately, the human confirming a claim) are what resolve the cases
# image similarity alone can't.
IMAGE_SIM_FLOOR = 0.55
IMAGE_SIM_CEILING = 0.95
TEXT_SIM_FLOOR = 0.25
TEXT_SIM_CEILING = 0.92


class MatchingEngine:
    def compute_match_score(
        self,
        source: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, float]:

        source_image = self._normalize_embedding(source.get("image_embedding"))
        candidate_image = self._normalize_embedding(candidate.get("image_embedding"))

        source_text = self._normalize_embedding(source.get("text_embedding"))
        candidate_text = self._normalize_embedding(candidate.get("text_embedding"))

        image_score = self._calibrate(
            self._embedding_similarity(source_image, candidate_image),
            IMAGE_SIM_FLOOR,
            IMAGE_SIM_CEILING,
        )
        text_score = self._calibrate(
            self._embedding_similarity(source_text, candidate_text),
            TEXT_SIM_FLOOR,
            TEXT_SIM_CEILING,
        )
        metadata_score = self._metadata_similarity(source, candidate)

        has_image = source_image is not None and candidate_image is not None
        has_text = source_text is not None and candidate_text is not None

        if has_image and has_text:
            final_score = (
                IMAGE_WEIGHT * image_score
                + TEXT_WEIGHT * text_score
                + METADATA_WEIGHT * metadata_score
            )
        elif has_image:
            final_score = 0.85 * image_score + 0.15 * metadata_score
        elif has_text:
            final_score = 0.85 * text_score + 0.15 * metadata_score
        else:
            final_score = metadata_score

        return {
            "confidence_score": round(min(max(final_score, 0.0), 1.0), 4),
            "image_score": round(image_score, 4),
            "text_score": round(text_score, 4),
            "metadata_score": round(metadata_score, 4),
        }

    def rank_matches(
        self,
        source: dict[str, Any],
        candidates: list[dict[str, Any]],
        top_k: int = 5,
        threshold: float = DEFAULT_MATCH_THRESHOLD,
    ) -> list[dict[str, Any]]:

        scored = []

        for candidate in candidates:
            scores = self.compute_match_score(source, candidate)
            if scores["confidence_score"] < threshold:
                continue
            scored.append({**candidate, **scores})

        scored.sort(key=lambda item: item["confidence_score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _normalize_embedding(vec):
        if vec is None:
            return None

        if isinstance(vec, str):
            # pgvector's `vector` type has no native PostgREST/JSON codec, so
            # Supabase always returns it as its Postgres text literal, e.g.
            # "[0.01,0.02,...]" (square brackets, pgvector's own format) -
            # NOT "{0.01,0.02,...}" (Postgres array-literal braces). Stripping
            # only "{}" left the brackets in place, so every real embedding
            # fetched from the DB failed float() and silently came back as
            # None - meaning image/text similarity never factored into a
            # match at all, and only metadata (location/time/title text)
            # could produce one.
            vec = vec.strip().strip("{}[]")
            try:
                return [float(x) for x in vec.split(",") if x.strip()]
            except ValueError:
                return None

        if isinstance(vec, list):
            try:
                return [float(x) for x in vec]
            except:
                return None

        return None

    @staticmethod
    def _embedding_similarity(
        vec_a: Optional[list[float]],
        vec_b: Optional[list[float]],
    ) -> float:

        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        similarity = dot / (norm_a * norm_b)
        return max(0.0, min(1.0, similarity))

    @staticmethod
    def _calibrate(raw_similarity: float, floor: float, ceiling: float) -> float:
        """Rescale a raw cosine similarity so the floor..ceiling band (where
        the actual discrimination happens) spans the full 0..1 range."""
        if raw_similarity <= floor:
            return 0.0
        if raw_similarity >= ceiling:
            return 1.0
        return (raw_similarity - floor) / (ceiling - floor)

    def _metadata_similarity(
        self,
        source: dict[str, Any],
        candidate: dict[str, Any],
    ) -> float:

        location_score = self._location_similarity(
            source.get("location", ""),
            candidate.get("location", ""),
        )

        time_score = self._time_similarity(
            source.get("item_timestamp"),
            candidate.get("item_timestamp"),
        )

        category_score = self._category_similarity(
            source.get("title", ""),
            source.get("description", ""),
            candidate.get("title", ""),
            candidate.get("description", ""),
            source.get("category"),
            candidate.get("category"),
        )

        return 0.40 * location_score + 0.35 * time_score + 0.25 * category_score

    @staticmethod
    def _location_similarity(loc_a: str, loc_b: str) -> float:
        if not loc_a or not loc_b:
            return 0.0

        a = loc_a.lower().strip()
        b = loc_b.lower().strip()

        if a == b:
            return 1.0

        tokens_a = set(re.findall(r"\w+", a))
        tokens_b = set(re.findall(r"\w+", b))

        if not tokens_a or not tokens_b:
            return SequenceMatcher(None, a, b).ratio()

        overlap = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)

        jaccard = overlap / union if union else 0.0
        fuzzy = SequenceMatcher(None, a, b).ratio()

        return max(jaccard, fuzzy * 0.8)

    @staticmethod
    def _time_similarity(
        time_a: Optional[str | datetime],
        time_b: Optional[str | datetime],
    ) -> float:

        if not time_a or not time_b:
            return 0.0

        try:
            if isinstance(time_a, str):
                time_a = datetime.fromisoformat(time_a.replace("Z", "+00:00"))

            if isinstance(time_b, str):
                time_b = datetime.fromisoformat(time_b.replace("Z", "+00:00"))

            diff_hours = abs((time_a - time_b).total_seconds()) / 3600

            if diff_hours <= 24:
                return 1.0
            if diff_hours <= 72:
                return 0.8
            if diff_hours <= 168:
                return 0.5
            if diff_hours <= 720:
                return 0.25

            return 0.1

        except:
            return 0.0

    @staticmethod
    def _category_similarity(
        title_a: str,
        desc_a: str,
        title_b: str,
        desc_b: str,
        cat_a: Optional[str],
        cat_b: Optional[str],
    ) -> float:

        if cat_a and cat_b:
            if cat_a.lower() == cat_b.lower():
                return 1.0
            return SequenceMatcher(None, cat_a.lower(), cat_b.lower()).ratio()

        combined_a = f"{title_a} {desc_a}".lower()
        combined_b = f"{title_b} {desc_b}".lower()

        return SequenceMatcher(None, combined_a, combined_b).ratio()