# ---------------------------------------------------------
# DATABASE SESSION
# ---------------------------------------------------------

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Pull the database URL from the environment (provided by Docker)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:supersecret@postgres:5432/ticketing_db"
)

# Create the async engine with a connection pool
engine = create_async_engine(DATABASE_URL, pool_size=20, max_overflow=10, echo=False)

# Create a factory that generates a fresh, isolated database session for each API request
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# This is the Base class that all our future models will inherit from
Base = declarative_base()

async def get_db():
    """Dependency injection function to provide a database session to FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session