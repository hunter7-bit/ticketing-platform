# ---------------------------------------------------------
# EVENT & TIER MODELS (SQL Tables: events, ticket_tiers)
# ---------------------------------------------------------

import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    venue = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships allow us to do things like: `my_event.tiers` to get all pricing levels
    tiers = relationship("TicketTier", back_populates="event", cascade="all, delete-orphan")

class TicketTier(Base):
    __tablename__ = "ticket_tiers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # ForeignKey links this tier back to a specific event
    event_id = Column(String, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    price = Column(Numeric(10,2), nullable=False)
    max_capacity = Column(Integer, nullable=False)
    remaining_capacity = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event = relationship("Event", back_populates="tiers")
    tickets = relationship("Ticket", back_populates="tier", cascade="all, delete-orphan")