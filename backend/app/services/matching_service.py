import logging
from typing import Any, Optional
from uuid import UUID

from ai.embeddings import EmbeddingService
from ai.matching import MatchingEngine

from app.config import Settings
from app.models import ItemResponse, MatchResult, MatchStatus
from app.services.email_service import EmailService
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class MatchingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = get_supabase_client()
        self.embedding_service = EmbeddingService()
        self.matching_engine = MatchingEngine()
        self.email_service = EmailService(settings)

    async def generate_and_store_embeddings(
        self,
        item_id: str,
        description: Optional[str],
        image_bytes: Optional[bytes],
    ) -> dict[str, Optional[list[float]]]:
        text_embedding = self.embedding_service.generate_text_embedding(description or "")
        image_embedding = None
        if image_bytes:
            image_embedding = self.embedding_service.generate_image_embedding(image_bytes)

        payload: dict[str, Any] = {"item_id": item_id}

        # Validate vector dimensions before writing (pgvector columns are 384/512
        # and will reject anything else; catch it here with a clear log instead).
        if text_embedding is not None:
            if len(text_embedding) == 384:
                payload["text_embedding"] = text_embedding
            else:
                logger.error(
                    "Text embedding for %s has wrong dim %d (expected 384); skipping",
                    item_id, len(text_embedding),
                )
        if image_embedding is not None:
            if len(image_embedding) == 512:
                payload["image_embedding"] = image_embedding
            else:
                logger.error(
                    "Image embedding for %s has wrong dim %d (expected 512); skipping",
                    item_id, len(image_embedding),
                )

        if len(payload) == 1:  # only item_id -> nothing generated
            logger.warning(
                "No embeddings generated for item %s (no usable text or image). "
                "This item will only match on metadata.",
                item_id,
            )

        self.client.table("embeddings").upsert(payload, on_conflict="item_id").execute()

        return {
            "text_embedding": text_embedding,
            "image_embedding": image_embedding,
        }

    async def find_matches(
        self,
        item_id: UUID,
        persist: bool = True,
    ) -> list[MatchResult]:
        source = self._get_item_with_embeddings(str(item_id))
        if not source:
            return []

        opposite_type = "found" if source["type"] == "lost" else "lost"
        candidates = self._fetch_candidates(source, opposite_type)

        ranked = self.matching_engine.rank_matches(
            source,
            candidates,
            top_k=self.settings.match_top_k,
            threshold=self.settings.match_threshold,
        )

        results: list[MatchResult] = []
        for match in ranked:
            matched_item = self._parse_item(match)
            result = MatchResult(
                item_id=item_id,
                matched_item_id=UUID(match["id"]),
                confidence_score=match["confidence_score"],
                image_score=match.get("image_score", 0.0),
                text_score=match.get("text_score", 0.0),
                metadata_score=match.get("metadata_score", 0.0),
                status=MatchStatus.PENDING,
                matched_item=matched_item,
            )

            if persist:
                stored, is_new = self._persist_match(item_id, result)
                result.id = stored.get("id")
                # Only fire notifications the first time a match is created, so
                # revisiting / re-scanning the results page never spams duplicates.
                if is_new:
                    await self._notify_match(source, match, result.confidence_score)

            results.append(result)

        if persist and results:
            self.client.table("items").update({"status": "matched"}).eq(
                "id", str(item_id)
            ).execute()

        return results

    def _get_item_with_embeddings(self, item_id: str) -> Optional[dict[str, Any]]:
        item_result = (
            self.client.table("items")
            .select("*")
            .eq("id", item_id)
            .single()
            .execute()
        )
        if not item_result.data:
            return None

        embedding_result = (
            self.client.table("embeddings")
            .select("image_embedding, text_embedding")
            .eq("item_id", item_id)
            .maybe_single()
            .execute()
        )

        item = item_result.data
        if embedding_result.data:
            item["image_embedding"] = embedding_result.data.get("image_embedding")
            item["text_embedding"] = embedding_result.data.get("text_embedding")

        return item

    def _fetch_candidates(
        self,
        source: dict[str, Any],
        opposite_type: str,
    ) -> list[dict[str, Any]]:
        limit = self.settings.match_candidate_limit
        image_embedding = source.get("image_embedding")
        text_embedding = source.get("text_embedding")

        candidate_ids: set[str] = set()
        candidates: list[dict[str, Any]] = []

        if image_embedding:
            image_candidates = self._vector_search(
                embedding=image_embedding,
                column="image_embedding",
                opposite_type=opposite_type,
                limit=limit,
            )
            for candidate in image_candidates:
                if candidate["id"] not in candidate_ids:
                    candidate_ids.add(candidate["id"])
                    candidates.append(candidate)

        if text_embedding:
            text_candidates = self._vector_search(
                embedding=text_embedding,
                column="text_embedding",
                opposite_type=opposite_type,
                limit=limit,
            )
            for candidate in text_candidates:
                if candidate["id"] not in candidate_ids:
                    candidate_ids.add(candidate["id"])
                    candidates.append(candidate)

        if not candidates:
            candidates = self._fetch_all_opposite(source["id"], opposite_type, limit)

        return candidates

    def _vector_search(
        self,
        embedding: list[float],
        column: str,
        opposite_type: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        try:
            response = self.client.rpc(
                "match_items_by_embedding",
                {
                    "query_embedding": embedding,
                    "embedding_column": column,
                    "match_type": opposite_type,
                    "match_count": limit,
                },
            ).execute()
            return response.data or []
        except Exception:
            logger.warning("Vector RPC unavailable, falling back to full scan")
            return self._fetch_all_opposite(None, opposite_type, limit)

    def _fetch_all_opposite(
        self,
        exclude_id: Optional[str],
        opposite_type: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        query = (
            self.client.table("items")
            .select("*, embeddings(image_embedding, text_embedding)")
            .eq("type", opposite_type)
            .eq("status", "active")
            .limit(limit)
        )
        if exclude_id:
            query = query.neq("id", exclude_id)

        result = query.execute()
        candidates = []
        for row in result.data or []:
            embedding = row.pop("embeddings", None) or {}
            row["image_embedding"] = embedding.get("image_embedding")
            row["text_embedding"] = embedding.get("text_embedding")
            candidates.append(row)
        return candidates

    def _persist_match(
        self, item_id: UUID, match: MatchResult
    ) -> tuple[dict[str, Any], bool]:
        """Upsert a match row. Returns (row, is_new) where is_new is True only if
        no match previously existed for this (item_id, matched_item_id) pair."""
        existing = (
            self.client.table("matches")
            .select("id")
            .eq("item_id", str(item_id))
            .eq("matched_item_id", str(match.matched_item_id))
            .limit(1)
            .execute()
        )
        is_new = not (existing.data)

        payload = {
            "item_id": str(item_id),
            "matched_item_id": str(match.matched_item_id),
            "confidence_score": match.confidence_score,
            "image_score": match.image_score,
            "text_score": match.text_score,
            "metadata_score": match.metadata_score,
            "status": match.status.value,
        }
        result = (
            self.client.table("matches")
            .upsert(payload, on_conflict="item_id,matched_item_id")
            .execute()
        )
        return (result.data[0] if result.data else {}), is_new

    async def _notify_match(
        self,
        source: dict[str, Any],
        candidate: dict[str, Any],
        confidence: float,
    ) -> None:
        user_id = source.get("user_id")
        user_result = (
            self.client.table("users")
            .select("email, name")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not user_result.data:
            return

        notification = {
            "user_id": user_id,
            "title": "Possible match found!",
            "message": (
                f"We found a possible match for '{source.get('title')}' "
                f"with '{candidate.get('title')}' "
                f"({confidence * 100:.0f}% confidence)."
            ),
            "type": "match",
            "related_item_id": source.get("id"),
        }
        self.client.table("notifications").insert(notification).execute()

        await self.email_service.send_match_notification(
            to_email=user_result.data["email"],
            item_title=source.get("title", "your item"),
            match_title=candidate.get("title", "a matched item"),
            confidence=confidence,
        )

        candidate_owner = (
            self.client.table("users")
            .select("email")
            .eq("id", candidate.get("user_id"))
            .single()
            .execute()
        )
        if candidate_owner.data:
            self.client.table("notifications").insert(
                {
                    "user_id": candidate.get("user_id"),
                    "title": "Your item may have been matched",
                    "message": (
                        f"Your item '{candidate.get('title')}' may match "
                        f"'{source.get('title')}'."
                    ),
                    "type": "match",
                    "related_item_id": candidate.get("id"),
                }
            ).execute()

    @staticmethod
    def _parse_item(data: dict[str, Any]) -> ItemResponse:
    	return ItemResponse(
        	id=data["id"],
        	user_id=data["user_id"],
        	type=data["type"],
        	title=data["title"],
        	description=data.get("description"),
        	location=data["location"],
        	item_timestamp=data["item_timestamp"],
        	image_url=data.get("image_url"),
        	category=data.get("category"),
        	status=data["status"],
        	created_at=data["created_at"],
        	updated_at=data["updated_at"],
    	)