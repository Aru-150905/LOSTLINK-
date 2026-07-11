from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ItemType(str, Enum):
    LOST = "lost"
    FOUND = "found"


class ItemStatus(str, Enum):
    ACTIVE = "active"
    MATCHED = "matched"
    CLAIMED = "claimed"
    RETURNED = "returned"
    RESOLVED = "resolved"


class ClaimStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MatchStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class UserProfile(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: Optional[str] = None
    is_admin: bool = False
    created_at: datetime


class ItemCreate(BaseModel):
    type: ItemType
    title: str = Field(min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    location: str = Field(min_length=2, max_length=500)

    item_timestamp: datetime

    category: Optional[str] = Field(default=None, max_length=100)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    contact_email: Optional[EmailStr] = None


class ItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: ItemType
    title: str
    description: Optional[str] = None
    location: str

    item_timestamp: datetime

    image_url: Optional[str] = None
    category: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    status: ItemStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"extra": "ignore"}


class MatchResult(BaseModel):
    id: Optional[UUID] = None
    item_id: UUID
    matched_item_id: UUID
    confidence_score: float
    image_score: float = 0.0
    text_score: float = 0.0
    metadata_score: float = 0.0
    status: MatchStatus = MatchStatus.PENDING
    matched_item: Optional[ItemResponse] = None


class UploadItemResponse(BaseModel):
    item: ItemResponse
    matches: list[MatchResult]


class EmbeddingRequest(BaseModel):
    text: Optional[str] = None


class EmbeddingResponse(BaseModel):
    text_embedding: Optional[list[float]] = None
    image_embedding: Optional[list[float]] = None


class SearchMatchesRequest(BaseModel):
    item_id: UUID


class SearchMatchesResponse(BaseModel):
    item_id: UUID
    matches: list[MatchResult]


class ClaimCreate(BaseModel):
    item_id: UUID
    message: Optional[str] = Field(default=None, max_length=1000)


class ClaimResponse(BaseModel):
    id: UUID
    item_id: UUID
    claimer_id: UUID
    message: Optional[str] = None
    status: ClaimStatus
    admin_notes: Optional[str] = None
    created_at: datetime


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    type: str
    read: bool
    related_item_id: Optional[UUID] = None
    related_match_id: Optional[UUID] = None
    created_at: datetime


class MarkResolvedRequest(BaseModel):
    item_id: UUID


class AdminClaimAction(BaseModel):
    claim_id: UUID
    action: ClaimStatus
    admin_notes: Optional[str] = None


class MessageResponse(BaseModel):
    message: str