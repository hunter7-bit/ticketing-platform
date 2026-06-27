# ---------------------------------------------------------
# AUTHENTICATION ENDPOINTS
# ---------------------------------------------------------
# This file handles user login and issuing JSON Web Tokens.

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.security import verify_password, create_access_token, get_password_hash
from app.db.session import get_db
from app.models.user import User

router = APIRouter()

# --- Pydantic Schema for the Response ---

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db) # We inject the database session here!
):
    """
    Authenticates a user and returns a JWT.
    """

    # 1. FIND THE USER IN THE DATABASE
    # We query the database to find the user by their email (form_data.username)
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalars().first()


    # 2. Verify the user exists
    if not user:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect email or password",
            headers = {"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Verify the password
    # We compare the plain text password they typed in with the hashed version in the DB.
    # In this mock, the correct password is "secret123"
    is_password_correct = verify_password(form_data.password, user.hashed_password)
    if not is_password_correct:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect email or password",
            headers = {"WWW-Authenticate": "Bearer"},
        )
    
    # 4.Create the JWT (The VIP Pass)
    # The user is legit! We pack their user ID into the JWT payload.
    # We use "sub" (subject), which is the industry standard key for user IDs in JWTs.
    jwt_payload = {"sub": user.id}
    access_token = create_access_token(data=jwt_payload)

    # 5. Return the token
    # The frontend will receive this token and save it (usually in memory or an HTTP-only cookie)
    return {"access_token": access_token, "token_type": "bearer"}