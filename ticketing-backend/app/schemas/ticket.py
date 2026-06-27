# ---------------------------------------------------------
# TICKET SCHEMAS (Data Validation)
# ---------------------------------------------------------

from pydantic import BaseModel
from datetime import datetime

class ReserveRequest(BaseModel):
    tier_id: str

class ReserveResponse(BaseModel):
    message : str
    ticket_id : str
    expires_at : datetime

class CheckoutRequest(BaseModel):
    ticket_id: str

class CheckoutResponse(BaseModel):
    message: str
    ticket_id: str
    status: str