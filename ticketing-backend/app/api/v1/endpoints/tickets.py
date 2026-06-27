# ---------------------------------------------------------
# TICKETS ENDPOINT
# ---------------------------------------------------------

import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from app.db.session import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import ReserveRequest, ReserveResponse,CheckoutRequest, CheckoutResponse
from app.api.dependencies import get_current_user
from app.api.v1.endpoints.websockets import manager

router = APIRouter()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

@router.post("/reserve", response_model=ReserveResponse)
async def reserve_ticket(
    request: ReserveRequest,
    db: AsyncSession = Depends(get_db),
    # THIS IS OUR SECURITY GUARD! It intercepts the JWT and returns the verified user ID
    current_user_id: str = Depends(get_current_user)
):
    """
    Finds an available ticket, locks it to the user, and starts the Redis expiration timer.
    """

    # 1. FIND AVAILABLE TICKET WITH SKIP LOCKED
    query = (
        select(Ticket)
        .where(Ticket.tier_id == request.tier_id, Ticket.status == "AVAILABLE")
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    result = await db.execute(query)
    ticket = result.scalars().first()

    # If no tickets are left (or all are temporarily locked), reject the request cleanly
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="High traffic: No tickets currently available for this tier."
        )
    # 2.Lock the ticket in postgres
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=10)

    ticket.status = "LOCKED"
    ticket.user_id = current_user_id
    ticket.locked_at = now

    await db.commit()

    # 3. START THE REDIS 15 Seconds TIMER
    # It sets a key like "ticket:lock:123" with a TTL (Time-To-Live) of 600 seconds.
    redis_client = await redis.from_url(REDIS_URL)
    await redis_client.setex(f"ticket:lock:{ticket.id}", 15, "locked")
    await redis_client.aclose() # Gracefully close the Redis connection

    # --- NEW: BROADCAST TO ALL USERS ---
    # Tell everyone's browser to instantly refresh their remaining ticket counts!
    await manager.broadcast("refresh_events")

    return ReserveResponse(
        message="Ticket reserved! You have 15 seconds to complete checkout.",
        ticket_id=ticket.id,
        expires_at=expires_at
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout_ticket(
    request: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user)
):
    """
    Completes the purchase of a locked ticket.
    """
    # 1. Verify the ticket is currently locked by THIS exact user
    query = select(Ticket).where(
        Ticket.id == request.ticket_id,
        Ticket.user_id == current_user_id,
        Ticket.status == "LOCKED"
    )

    result = await db.execute(query)
    ticket = result.scalars().first()

    # If the worker already unlocked it, or it's not theirs, reject.
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkout failed: Ticket reservation expired or invalid."
        )
    
    # 2. Complete the purchase
    ticket.status = "SOLD"
    await db.commit()

    # --- NEW: BROADCAST TO ALL USERS ---
    await manager.broadcast("refresh_events")


    return CheckoutResponse(
        message="Payment successful! Enjoy the festival.",
        ticket_id=ticket.id,
        status=ticket.status
    )
    