# ---------------------------------------------------------
# DATABASE SEEDER
# ---------------------------------------------------------
# This script populates our database with dummy data so we 
# have events to view and tickets to reserve.

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.event import Event, TicketTier
from app.models.ticket import Ticket
from app.core.security import get_password_hash

async def seed_database():
    # Open an asynchronous connection to Postgres
    async with AsyncSessionLocal() as session:
        print("Starting database seeding...")

        # 1. CREATE A TEST USER
        # We need a user in the database so our /login endpoint actually works
        user_id = str(uuid.uuid4())
        test_email = "test@example.com"
        test_user = User(
            id=user_id,
            email=test_email,
            hashed_password=get_password_hash("secret123")
        )
        session.add(test_user)
        print(f"[OK] Created test user: {test_email} (Password: secret123)")

        # 2. CREATE A CONCERT EVENT
        event_id = str(uuid.uuid4())
        event = Event(
            id=event_id,
            title="Oikotaan Music Festival 2026",
            description="The biggest tech and music festival of the year.",
            start_time=datetime.now(timezone.utc) + timedelta(days=30),
            venue="Main Campus Stadium"
        )
        session.add(event)
        print(f"[OK] Created event: {event.title}")

        # 3. CREATE TICKET TIERS
        # We make a VIP tier with very few tickets so we can test what 
        # happens when it "sells out" quickly.
        vip_tier_id = str(uuid.uuid4())
        vip_tier = TicketTier(
            id=vip_tier_id,
            event_id=event_id,
            name="VIP Pass",
            price=150.00,
            max_capacity=5,  # Only 5 VIP passes available!
            remaining_capacity=5
        )
        
        ga_tier_id = str(uuid.uuid4())
        ga_tier = TicketTier(
            id=ga_tier_id,
            event_id=event_id,
            name="General Admission",
            price=50.00,
            max_capacity=100, # 100 regular passes
            remaining_capacity=100
        )
        session.add_all([vip_tier, ga_tier])
        print(f"[OK] Created tiers: VIP Pass (5 seats) & General Admission (100 seats)")

        # 4. PRE-ALLOCATE THE ACTUAL TICKET ROWS
        # This is our production strategy! Instead of just decrementing a counter,
        # we create 105 individual ticket rows that our `skip_locked` query can grab.
        tickets_to_insert = []
        
        for _ in range(vip_tier.max_capacity):
            tickets_to_insert.append(Ticket(tier_id=vip_tier_id, status="AVAILABLE"))
            
        for _ in range(ga_tier.max_capacity):
            tickets_to_insert.append(Ticket(tier_id=ga_tier_id, status="AVAILABLE"))
            
        session.add_all(tickets_to_insert)
        print(f"[OK] Pre-allocated {len(tickets_to_insert)} individual ticket rows.")

        # Commit all the transactions to the database
        await session.commit()
        print("Database seeding completed successfully! You are ready to go.")

if __name__ == "__main__":
    # Execute the async function
    asyncio.run(seed_database())