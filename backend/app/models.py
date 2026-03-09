import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from .config import settings
from .db import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="new")
    tags = Column(ARRAY(String), nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    last_message_at = Column(DateTime, nullable=True)

    conversations = relationship("Conversation", back_populates="lead")
    messages = relationship("Message", back_populates="lead")
    status_history = relationship(
        "LeadStatusHistory",
        back_populates="lead",
        cascade="all, delete-orphan",
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    channel = Column(String(50), nullable=False)
    external_user_id = Column(String(128), nullable=True)
    external_chat_id = Column(String(128), nullable=True)
    state = Column(JSONB, nullable=False, default=dict)
    last_inbound_at = Column(DateTime, nullable=True)
    last_outbound_at = Column(DateTime, nullable=True)

    lead = relationship("Lead", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
    )
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    channel = Column(String(50), nullable=False)
    direction = Column(String(16), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivery_status = Column(String(32), nullable=False, default="unknown")
    delivery_error = Column(Text, nullable=True)
    extra = Column("metadata", JSONB, nullable=False, default=dict)

    conversation = relationship("Conversation", back_populates="messages")
    lead = relationship("Lead", back_populates="messages")


class LeadStatusHistory(Base):
    __tablename__ = "lead_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(Text, nullable=True)
    reason_code = Column(String(64), nullable=True)

    lead = relationship("Lead", back_populates="status_history")


class LostReason(Base):
    __tablename__ = "lost_reasons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)


class KbArticle(Base):
    __tablename__ = "kb_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(128), unique=True, nullable=True)
    title = Column(String(255), nullable=False, unique=True)
    category = Column(String(64), nullable=False, default="general")
    content = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    embedding = relationship(
        "KbEmbedding",
        uselist=False,
        back_populates="article",
        cascade="all, delete-orphan",
    )


class KbEmbedding(Base):
    __tablename__ = "kb_embeddings"

    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("kb_articles.id"),
        primary_key=True,
    )
    embedding = Column(JSONB, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("KbArticle", back_populates="embedding")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    tags = Column(ARRAY(String), nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ReplyTemplate(Base):
    __tablename__ = "reply_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(128), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    channel = Column(String(32), nullable=True)
    intent = Column(String(64), nullable=False)
    risk_level = Column(String(16), nullable=False, default="low")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=True)
    slot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("available_slots.id"),
        nullable=True,
    )
    status = Column(String(50), nullable=False, default="requested")
    scheduled_at = Column(DateTime, nullable=True)
    contact_name = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_message = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="web")
    cancel_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class AvailableSlot(Base):
    __tablename__ = "available_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False, default=1)
    reserved_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ReminderQueueItem(Base):
    __tablename__ = "reminders_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id"),
        nullable=False,
    )
    remind_at = Column(DateTime, nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(64), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

