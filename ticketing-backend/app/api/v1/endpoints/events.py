from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List

from app.db.session import get_db
from app.models.event import Event
from app.models.ticket import Ticket
from app.schemas.event import EventSchema

router = APIRouter()

@router.get("/", response_model=List[EventSchema])
async def get_events(db: AsyncSession = Depends(get_db)):
    """
    Fetches all active events and their ticket tiers to display on the frontend.
    """

    # selectionhead
    # It grabs all the events AND their ticket tiers in just 2 queries, 
    # preventing the dreaded "N+1 query problem" that slows down databases.
    query = select(Event).options(selectinload(Event.tiers))

    result = await db.execute(query)
    events = result.scalars().all()

    for event in events:
        for tier in event.tiers:
            count_query = select(func.count()).where(
                Ticket.tier_id == tier.id, 
                Ticket.status == "AVAILABLE"
            )
            count_result = await db.execute(count_query)
            # Temporarily overwrite the property in memory before sending to frontend
            tier.remaining_capacity = count_result.scalar()

    return events

