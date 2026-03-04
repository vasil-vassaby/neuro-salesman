from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool


class ConfigResponse(BaseModel):
    app_url: str
    web_url: str
    rag_enabled: bool
    telegram_mode: str


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


class SendMessageRequest(BaseModel):
    text: str


class WebLeadRequest(BaseModel):
    name: str
    phone: str
    message: str


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
        orm_mode = True


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
        orm_mode = True


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
        orm_mode = True

