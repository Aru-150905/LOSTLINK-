from uuid import UUID

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import get_current_user
from app.models import ClaimCreate, ClaimResponse, MarkResolvedRequest, MessageResponse
from app.services.item_service import ItemService

router = APIRouter(tags=["claims"])


@router.post("/claim-item", response_model=ClaimResponse)
async def claim_item(
    payload: ClaimCreate,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    return await service.create_claim(current_user["id"], payload)


@router.post("/mark-resolved")
async def mark_resolved(
    payload: MarkResolvedRequest,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    item = await service.mark_resolved(current_user["id"], payload)
    return {"item": item, "message": "Item marked as returned"}
