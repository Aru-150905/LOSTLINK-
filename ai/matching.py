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
DEFAULT_MATCH_THRESHOLD = 0.35


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

        image_score = self._embedding_similarity(source_image, candidate_image)
        text_score = self._embedding_similarity(source_text, candidate_text)
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
            vec = vec.strip("{}")
            try:
                return [float(x) for x in vec.split(",")]
            except:
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