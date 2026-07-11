import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from app.config import Settings
from app.models import (
    ClaimCreate,
    ClaimResponse,
    ClaimStatus,
    ItemCreate,
    ItemResponse,
    ItemStatus,
    MarkResolvedRequest,
    MatchResult,
    NotificationResponse,
    UploadItemResponse,
)
from app.services.email_service import EmailService
from app.services.matching_service import MatchingService
from app.services.storage_service import StorageService
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ItemService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = get_supabase_client()
        self.storage = StorageService(settings)
        self.matching = MatchingService(settings)
        self.email = EmailService(settings)

    async def upload_item(
        self,
        user_id: str,
        payload: ItemCreate,
        image: Optional[UploadFile],
    ) -> UploadItemResponse:
        if payload.type.value == "found" and not image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image is required for found items",
            )

        image_url = None
        image_bytes = None
        if image:
            content_type = (image.content_type or "").lower()
            if not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Uploaded file must be an image (got '{content_type or 'unknown'}')",
                )

            image_bytes = await image.read()
            if not image_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Empty image file",
                )
            if len(image_bytes) > self.settings.max_image_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image exceeds max size of {self.settings.max_image_bytes // (1024*1024)}MB",
                )

            try:
                image_url = await self.storage.upload_image(
                    user_id=user_id,
                    file_bytes=image_bytes,
                    filename=image.filename or "upload.jpg",
                    content_type=content_type or "image/jpeg",
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.exception("Image upload to storage failed")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Image upload failed. Check that the storage bucket exists and is reachable.",
                ) from exc

        item_data = {
            "user_id": user_id,
            "type": payload.type.value,
            "title": payload.title,
            "description": payload.description,
            "location": payload.location,
            "item_timestamp": payload.item_timestamp.isoformat(),
            "image_url": image_url,
            "category": payload.category,
            "contact_phone": payload.contact_phone,
            "contact_email": payload.contact_email,
            "status": ItemStatus.ACTIVE.value,
        }

        result = self.client.table("items").insert(item_data).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create item",
            )

        item = result.data[0]
        await self.matching.generate_and_store_embeddings(
            item_id=item["id"],
            description=payload.description or payload.title,
            image_bytes=image_bytes,
        )

        matches = await self.matching.find_matches(UUID(item["id"]))

        return UploadItemResponse(
            item=self._parse_item(item),
            matches=matches,
        )

    async def get_my_items(self, user_id: str) -> list[ItemResponse]:
        result = (
            self.client.table("items")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [self._parse_item(row) for row in result.data or []]

    async def search_matches(self, item_id: UUID, user_id: str) -> list[MatchResult]:
        item = (
            self.client.table("items")
            .select("user_id")
            .eq("id", str(item_id))
            .single()
            .execute()
        )
        if not item.data:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return await self.matching.find_matches(item_id, persist=True)

    async def get_stored_matches(self, item_id: UUID, user_id: str) -> list[MatchResult]:
        item = (
            self.client.table("items")
            .select("user_id")
            .eq("id", str(item_id))
            .single()
            .execute()
        )
        if not item.data:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        matches_result = (
            self.client.table("matches")
            .select("*")
            .eq("item_id", str(item_id))
            .order("confidence_score", desc=True)
            .execute()
        )

        results: list[MatchResult] = []
        for row in matches_result.data or []:
            matched_item_result = (
                self.client.table("items")
                .select("*")
                .eq("id", row["matched_item_id"])
                .single()
                .execute()
            )
            matched_item = (
                self._parse_item(matched_item_result.data)
                if matched_item_result.data
                else None
            )
            results.append(
                MatchResult(
                    id=row["id"],
                    item_id=row["item_id"],
                    matched_item_id=row["matched_item_id"],
                    confidence_score=row["confidence_score"],
                    image_score=row.get("image_score", 0),
                    text_score=row.get("text_score", 0),
                    metadata_score=row.get("metadata_score", 0),
                    status=row["status"],
                    matched_item=matched_item,
                )
            )
        return results

    async def create_claim(
        self,
        user_id: str,
        payload: ClaimCreate,
    ) -> ClaimResponse:
        item = (
            self.client.table("items")
            .select("*, users!items_user_id_fkey(email, name)")
            .eq("id", str(payload.item_id))
            .single()
            .execute()
        )
        if not item.data:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.data["user_id"] == user_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot claim your own item",
            )

        claim_data = {
            "item_id": str(payload.item_id),
            "claimer_id": user_id,
            "message": payload.message,
            "status": ClaimStatus.PENDING.value,
        }
        result = self.client.table("claims").insert(claim_data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create claim")

        claim = result.data[0]

        self.client.table("items").update({"status": "claimed"}).eq(
            "id", str(payload.item_id)
        ).execute()

        owner = item.data.get("users") or {}
        claimer = (
            self.client.table("users")
            .select("name, email")
            .eq("id", user_id)
            .single()
            .execute()
        )

        self.client.table("notifications").insert(
            {
                "user_id": item.data["user_id"],
                "title": "New claim on your item",
                "message": f"{claimer.data.get('name', 'Someone')} wants to claim '{item.data['title']}'.",
                "type": "claim",
                "related_item_id": str(payload.item_id),
            }
        ).execute()

        if owner.get("email"):
            await self.email.send_claim_notification(
                to_email=owner["email"],
                item_title=item.data["title"],
                claimer_name=claimer.data.get("name", "A user"),
            )

        return ClaimResponse(**claim)

    async def mark_resolved(
        self,
        user_id: str,
        payload: MarkResolvedRequest,
    ) -> ItemResponse:
        item = (
            self.client.table("items")
            .select("*")
            .eq("id", str(payload.item_id))
            .single()
            .execute()
        )
        if not item.data:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.data["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        result = (
            self.client.table("items")
            .update({"status": ItemStatus.RETURNED.value})
            .eq("id", str(payload.item_id))
            .execute()
        )

        self.client.table("notifications").insert(
            {
                "user_id": user_id,
                "title": "Item marked as returned",
                "message": f"'{item.data['title']}' has been marked as returned.",
                "type": "status",
                "related_item_id": str(payload.item_id),
            }
        ).execute()

        return self._parse_item(result.data[0])

    async def get_notifications(self, user_id: str) -> list[NotificationResponse]:
        result = (
            self.client.table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [NotificationResponse(**row) for row in result.data or []]

    async def mark_notification_read(self, user_id: str, notification_id: UUID) -> None:
        self.client.table("notifications").update({"read": True}).eq(
            "id", str(notification_id)
        ).eq("user_id", user_id).execute()

    async def get_pending_claims(self) -> list[dict]:
        result = (
            self.client.table("claims")
            .select("*, items(*), users!claims_claimer_id_fkey(name, email)")
            .eq("status", ClaimStatus.PENDING.value)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def review_claim(
        self,
        claim_id: UUID,
        action: ClaimStatus,
        admin_notes: Optional[str] = None,
    ) -> ClaimResponse:
        if action == ClaimStatus.PENDING:
            raise HTTPException(status_code=400, detail="Invalid action")

        claim = (
            self.client.table("claims")
            .select("*, items(title, user_id), users!claims_claimer_id_fkey(email)")
            .eq("id", str(claim_id))
            .single()
            .execute()
        )
        if not claim.data:
            raise HTTPException(status_code=404, detail="Claim not found")

        result = (
            self.client.table("claims")
            .update(
                {
                    "status": action.value,
                    "admin_notes": admin_notes,
                }
            )
            .eq("id", str(claim_id))
            .execute()
        )

        if action == ClaimStatus.APPROVED:
            self.client.table("items").update({"status": "resolved"}).eq(
                "id", claim.data["item_id"]
            ).execute()

        claimer_email = claim.data.get("users", {}).get("email")
        item_title = claim.data.get("items", {}).get("title", "item")
        if claimer_email:
            await self.email.send_claim_status_notification(
                to_email=claimer_email,
                item_title=item_title,
                approved=action == ClaimStatus.APPROVED,
            )

        return ClaimResponse(**result.data[0])

    async def get_admin_stats(self) -> dict:
        items = self.client.table("items").select("type, status", count="exact").execute()
        claims = (
            self.client.table("claims")
            .select("status", count="exact")
            .eq("status", ClaimStatus.PENDING.value)
            .execute()
        )
        matches = self.client.table("matches").select("id", count="exact").execute()

        all_items = self.client.table("items").select("type, status").execute()
        lost = sum(1 for i in all_items.data or [] if i["type"] == "lost")
        found = sum(1 for i in all_items.data or [] if i["type"] == "found")
        active = sum(1 for i in all_items.data or [] if i["status"] == "active")

        return {
            "total_items": items.count or 0,
            "lost_items": lost,
            "found_items": found,
            "active_items": active,
            "pending_claims": claims.count or 0,
            "total_matches": matches.count or 0,
        }

    @staticmethod
    def _parse_item(data: dict) -> ItemResponse:
        return ItemResponse(**data)
