from uuid import UUID

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import get_current_user
from app.services.item_service import ItemService

router = APIRouter(tags=["notifications"])


@router.get("/notifications")
async def get_notifications(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    notifications = await service.get_notifications(current_user["id"])
    unread = sum(1 for n in notifications if not n.read)
    return {"notifications": notifications, "unread_count": unread}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    await service.mark_notification_read(current_user["id"], notification_id)
    return {"message": "Notification marked as read"}
