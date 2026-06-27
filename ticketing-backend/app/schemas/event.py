from pydantic import BaseModel
from datetime import datetime
from typing import List

# We define the Tier schema first so we can nest it inside the Event schema
class TicketTierSchema(BaseModel):
    id: str
    name: str
    price: float
    remaining_capacity: int
    max_capacity: int

    class Config:
        from_attributes = True

class EventSchema(BaseModel):
    id: str
    title: str
    description: str
    start_time: datetime
    venue: str
    
    # This automatically fetches and nests all the pricing tiers for this event!
    tiers: List[TicketTierSchema]

    class Config:
        from_attributes = True