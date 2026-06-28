# ---------------------------------------------------------
# FASTAPI ENTRYPOINT
# ---------------------------------------------------------
# This is the file that Uvicorn (our web server) runs. 
# It glues all our disparate routes and middleware together.

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import database engine and Base to create tables on startup
from app.db.session import engine, Base
import app.models

# Import our individual feature routers
from app.api.v1.endpoints import auth, tickets, events, websockets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.info("🚀 Initiating database startup sequence...")
    
    # Explicitly import models inside the function to absolutely guarantee 
    # SQLAlchemy registers them in Base.metadata before create_all is called.
    from app.models.user import User
    from app.models.event import Event, TicketTier
    from app.models.ticket import Ticket
    from app.db.session import engine, Base
    
    try:
        async with engine.begin() as conn:
            logger.info("📦 Creating missing database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables verified/created successfully!")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        
    yield
    
    # --- SHUTDOWN LOGIC ---
    logger.info("🛑 API Shutting down...")


app = FastAPI(
    title="High-Concurrency Ticketing API",
    description="A ticketing app with row-level locking.",
    version="1.0.0",
)

# ---------------------------------------------------------
# CORS MIDDLEWARE
# ---------------------------------------------------------
# This allows our future React/Tailwind frontend to communicate with this API.
origins = [
    "http://localhost:3000",  # Standard React/Next.js local port
    "http://localhost:5173",  # Standard Vite (React) local port
    # "https://www.yourproductiondomain.com" # Will add this before launching
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# ---------------------------------------------------------
# ROUTER REGISTRATION
# ---------------------------------------------------------
# We attach our auth router and give it a prefix so every URL 
# automatically starts with /api/v1/auth/...
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["Tickets"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])

# ADD WEBSOCKETS ROUTER (Notice it has no prefix, so it sits at /api/v1/ws)
app.include_router(websockets.router, prefix="/api/v1", tags=["WebSockets"])
# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """
    Cloud providers like AWS or Kubernetes 
    will ping this endpoint every 10 seconds. If it stops returning "healthy", 
    the cloud automatically kills the crashed server and starts a fresh one.
    """
    return {"status": "healthy", "version": "1.0.0"}