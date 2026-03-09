from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool


class ConfigResponse(BaseModel):
    app_url: str
    web_url: str
    rag_enabled: bool
    telegram_mode: str
    reminder_hours_before: int


class MessageBase(BaseModel):
    id: UUID
    direction: str
    text: str
    created_at: datetime
    delivery_status: str
    delivery_error: Optional[str]


class LeadSummary(BaseModel):
    id: UUID
    display_name: str
    status: str


class ConversationSummary(BaseModel):
    id: UUID
    lead: LeadSummary
    channel: str
    last_message_text: Optional[str]
    last_message_at: Optional[datetime]


class ConversationDetail(BaseModel):
    id: UUID
    lead: LeadSummary
    channel: str
    messages: List[MessageBase]
    state: dict[str, Any]


class SendMessageRequest(BaseModel):
    text: str


class WebLeadRequest(BaseModel):
    name: str
    phone: str
    message: str


class WebBookingRequest(BaseModel):
    name: str
    phone: str
    message: str
    slot_id: UUID
    offer_id: Optional[UUID] = None


class AvailableSlotOut(BaseModel):
    id: UUID
    starts_at: datetime
    ends_at: datetime
    capacity: int
    reserved_count: int
    is_active: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


class AvailableSlotCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    capacity: int = 1
    notes: Optional[str] = None


class AvailableSlotUpdate(BaseModel):
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    capacity: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class BookingOut(BaseModel):
    id: UUID
    lead_id: UUID
    offer_id: Optional[UUID]
    slot_id: Optional[UUID]
    status: str
    scheduled_at: Optional[datetime]
    contact_name: str
    contact_phone: str
    contact_message: Optional[str]
    source: str
    cancel_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    status: str
    cancel_reason: Optional[str] = None


class LeadLostRequest(BaseModel):
    reason_code: str
    note: Optional[str] = None


class KbArticleBase(BaseModel):
    title: str
    category: str
    content: str
    active: bool = True


class KbArticleCreate(KbArticleBase):
    external_id: Optional[str] = None


class KbArticleUpdate(BaseModel):
    title: Optional[str]
    category: Optional[str]
    content: Optional[str]
    active: Optional[bool]


class KbArticleOut(KbArticleBase):
    id: UUID
    external_id: Optional[str]

    class Config:
        from_attributes = True


class OfferBase(BaseModel):
    title: str
    description: str
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    duration_minutes: Optional[int] = None
    active: bool = True
    tags: List[str] = []


class OfferCreate(OfferBase):
    pass


class OfferUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    price_min: Optional[float]
    price_max: Optional[float]
    duration_minutes: Optional[int]
    active: Optional[bool]
    tags: Optional[List[str]]


class OfferOut(OfferBase):
    id: UUID

    class Config:
        from_attributes = True


class ReplyTemplateBase(BaseModel):
    key: str
    title: str
    text: str
    channel: Optional[str] = None
    intent: str
    risk_level: str = "low"
    active: bool = True


class ReplyTemplateCreate(ReplyTemplateBase):
    pass


class ReplyTemplateUpdate(BaseModel):
    key: Optional[str]
    title: Optional[str]
    text: Optional[str]
    channel: Optional[str]
    intent: Optional[str]
    risk_level: Optional[str]
    active: Optional[bool]


class ReplyTemplateOut(ReplyTemplateBase):
    id: UUID

    class Config:
        from_attributes = True

