import logging
import uuid
from typing import Optional

from app.config import Settings
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = get_supabase_client()

    async def upload_image(
        self,
        user_id: str,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        path = f"{user_id}/{uuid.uuid4()}.{ext}"

        self.client.storage.from_(self.settings.storage_bucket).upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "false"},
        )

        return self.client.storage.from_(self.settings.storage_bucket).get_public_url(path)

    async def delete_image(self, image_url: str) -> None:
        if not image_url:
            return

        bucket = self.settings.storage_bucket
        marker = f"/storage/v1/object/public/{bucket}/"
        if marker not in image_url:
            return

        path = image_url.split(marker, 1)[1]
        try:
            self.client.storage.from_(bucket).remove([path])
        except Exception:
            logger.exception("Failed to delete image at %s", path)
