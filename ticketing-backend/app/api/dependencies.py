# ---------------------------------------------------------
# API DEPENDENCIES (The Security Guard)
# ---------------------------------------------------------
# Destination Folder: app/api/dependencies.py
# ---------------------------------------------------------
# This file contains reusable components that run BEFORE your 
# API endpoints. It is primarily used to extract and verify JWTs.

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel

# Import the exact same SECRET_KEY and ALGORITHM we used to create the token
from app.core.security import SECRET_KEY, ALGORITHM

# 1. The Token Extractor
# OAuth2PasswordBearer automatically looks at the incoming HTTP request.
# It searches for a header that looks like: "Authorization: Bearer <token>"
# If it finds it, it extracts the <token> part. If it doesn't, it automatically
# blocks the user with a 401 Unauthorized error.
# The `tokenUrl` tells Swagger UI where the login endpoint is so you can test it in the browser.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/api/v1/auth/login")

# --- Pydantic Schema for the Token Payload ---
class TokenData(BaseModel):
    user_id: str | None = None

# 2. The Security guard function
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    This function catches the token, decodes it, and verifies it hasn't 
    been tampered with. If valid, it returns the User ID.
    """

    # We create a standard HTTP 401 error to throw if anything goes wrong
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 3. DECODE AND VERIFY
        # We try to open the token using our top-secret key.
        # If a hacker changed even a single letter of the token, the math will fail,
        # and jwt.decode() will throw a JWTError.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract the user ID (which we stored under the key "sub" during login)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id)
    
    except JWTError:
        # This catches expired tokens, tampered tokens, or completely fake tokens.
        raise credentials_exception
    
    # 4. DATABASE CHECK
    # Right now, we are just returning the ID from the token.
    # In a fully connected app, we would query the database here to ensure
    # the user hasn't been deleted or banned since the token was issued:
    #
    # user = await db.execute(select(User).where(User.id == token_data.user_id))
    # if not user:
    #     raise credentials_exception
    # return user

    # For now, we return the verified user ID extracted from the token
    return token_data.user_id