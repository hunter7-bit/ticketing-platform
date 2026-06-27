# ---------------------------------------------------------
# TICKET MODEL (SQL Table: tickets)
# ---------------------------------------------------------

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tier_id = Column(String, ForeignKey("ticket_tiers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # nullable=True because when a ticket is first created, nobody owns it yet
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # We index the status column heavily because our skip_locked query scans it constantly
    status = Column(String(20), default="AVAILABLE", nullable=False, index=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tier = relationship("TicketTier", back_populates="tickets")
    user = relationship("User")