from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ai.embeddings import EmbeddingService
from app.config import Settings, get_settings
from app.dependencies import get_current_user
from app.models import (
    EmbeddingRequest,
    EmbeddingResponse,
    ItemCreate,
    SearchMatchesRequest,
    SearchMatchesResponse,
    UploadItemResponse,
)
from app.services.item_service import ItemService

router = APIRouter(tags=["items"])


@router.post("/upload-item", response_model=UploadItemResponse)
async def upload_item(
    type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    location: str = Form(...),
    timestamp: str = Form(...),
    category: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    from datetime import datetime

    payload = ItemCreate(
        type=type,
        title=title,
        description=description,
        location=location,
        item_timestamp=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
        category=category,
        contact_phone=contact_phone,
        contact_email=contact_email,
    )

    service = ItemService(settings)
    return await service.upload_item(current_user["id"], payload, image)


@router.post("/generate-embedding", response_model=EmbeddingResponse)
async def generate_embedding(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    embedding_service = EmbeddingService()
    text_embedding = None
    image_embedding = None

    if text:
        text_embedding = embedding_service.generate_text_embedding(text)
    if image:
        image_bytes = await image.read()
        image_embedding = embedding_service.generate_image_embedding(image_bytes)

    return EmbeddingResponse(
        text_embedding=text_embedding,
        image_embedding=image_embedding,
    )


@router.post("/search-matches", response_model=SearchMatchesResponse)
async def search_matches(
    payload: SearchMatchesRequest,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    matches = await service.search_matches(payload.item_id, current_user["id"])
    return SearchMatchesResponse(item_id=payload.item_id, matches=matches)


@router.get("/matches/{item_id}", response_model=SearchMatchesResponse)
async def get_matches(
    item_id: UUID,
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Read-only: return already-computed matches without re-running the search
    (so opening the results page never re-persists matches or re-sends notifications)."""
    service = ItemService(settings)
    matches = await service.get_stored_matches(item_id, current_user["id"])
    return SearchMatchesResponse(item_id=item_id, matches=matches)


@router.get("/my-items")
async def my_items(
    current_user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    service = ItemService(settings)
    items = await service.get_my_items(current_user["id"])
    return {"items": items}
