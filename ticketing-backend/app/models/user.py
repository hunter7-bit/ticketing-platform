# ---------------------------------------------------------
# USER MODEL (SQL Table: users)
# ---------------------------------------------------------

import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    # We use a UUID string so IDs are unguessable
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # func.now() tells Postgres to automatically stamp the exact creation time
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)