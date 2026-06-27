# ---------------------------------------------------------
# REDIS BACKGROUND WORKER
# ---------------------------------------------------------
# This script runs independently from our main FastAPI app. 
# Its only job is to listen for Redis expiration events and 
# unlock tickets in the PostgreSQL database.

import asyncio
import os
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# --- Configuration ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL","postgresql+asyncpg://user:password@localhost/ticketing_db")

#Setup PostgreSQL Connection
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def unlock_ticket_in_db(ticket_id: str):
    """
    Connects to Postgres and reverts a
    ticket status to AVAILABLE
    """
    async with AsyncSessionLocal() as session:
        # We use a raw SQL query here for speed and simplicity in the worker
        # We only unlock it if it is still 'LOCKED'. (If it's 'SOLD', we leave it alone)
        query = text("""
                     UPDATE tickets
                     SET status = 'AVAILABLE', user_id = NULL, locked_at = NULL
                     WHERE id = :ticket_id AND status = 'LOCKED'
                     """)
        await session.execute(query,{"ticket_id":ticket_id})
        await session.commit()
        print(f"[SUCCESS] Ticket {ticket_id} lock expired. Reverted to AVAILABLE.")
    

async def listen_for_expirations():
        """Subscribes to Redis Keyspace Notifications for expired keys."""
        print("Starting Redis Lock Manager Worker...")

        # Connect to Redis
        redis_client = await redis.from_url(REDIS_URL)

        # By default, Redis does NOT publish expiration events (to save CPU)
        # We must explicitly tell Redis to enable them using 'CONFIG SET'
        # 'Ex' means "Publish (E)vents for e(x)pired keys"
        await redis_client.config_set('notify-keyspace-events', 'Ex')

        # Set up the Pub/Sub Listener
        pubsub = redis_client.pubsub()

        # Subscribe to the specific Redis channel that broadcasts expired keys
        # '0' is the default Redis database index
        await pubsub.subscribe('__keyevent@0__:expired')

        print("Listening for expired ticket locks...")

        # Infinite loop to keep the worker alive and listening
        async for message in pubsub.listen():
            if message['type'] == 'message':
                # The message 'data' contains the name of the key that expired
                expired_key = message['data'].decode('utf-8')

                # Check if this expired key is a ticket lock
                if expired_key.startswith("ticket:lock:"):
                    # Extract the ticket ID from the key string (e.g., "ticket:lock:123" -> "123")
                    ticket_id = expired_key.split(":")[-1]
                    print(f"[EVENT] Redis TTL expired for ticket: {ticket_id}")

                    # Trigger the database unlock asynchronously
                    await unlock_ticket_in_db(ticket_id)

if __name__ == "__main__":
     # Start the asynchronous event loop
    try:
        asyncio.run(listen_for_expirations())
    except KeyboardInterrupt:
         print("\nWorker shutting down gracefully.")
    
    