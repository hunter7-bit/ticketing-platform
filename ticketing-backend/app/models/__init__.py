# ---------------------------------------------------------
# MODEL REGISTRY
# ---------------------------------------------------------

# By importing everything here, Alembic can read this single file 
# and automatically discover every table in our entire application.

from app.db.session import Base
from app.models.user import User
from app.models.event import Event, TicketTier
from app.models.ticket import Ticket