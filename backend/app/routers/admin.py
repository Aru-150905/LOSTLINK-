from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.dependencies import get_admin_user
from app.models import AdminClaimAction, ClaimResponse
from app.services.item_service import ItemService

router = APIRouter(tags=["admin"], prefix="/admin")


@router.get("/stats")
async def admin_stats(
    _: dict = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    return await service.get_admin_stats()


@router.get("/claims")
async def pending_claims(
    _: dict = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    claims = await service.get_pending_claims()
    return {"claims": claims}


@router.post("/claims/review", response_model=ClaimResponse)
async def review_claim(
    payload: AdminClaimAction,
    _: dict = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    return await service.review_claim(
        payload.claim_id,
        payload.action,
        payload.admin_notes,
    )
