from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.db.session import get_db
from app.models.event import Event
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

    return events

