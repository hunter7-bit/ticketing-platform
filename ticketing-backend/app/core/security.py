# ---------------------------------------------------------
# API SECURITY UTILITIES
# ---------------------------------------------------------
# This module handles password hashing (Bcrypt) and 
# the creation/verification of JSON Web Tokens (JWT).

from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt 

SECRET_KEY = "super_secret_production_key_do_not_share_this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Tokens expire fast to limit security risks

# Bcrypt is the industry standard for password hashing.
# It uses "salting" to ensure two users with the password "password123"
# will have completely different hashes stored in the database.

def verify_password(plain_password: str, hashed_password:str) -> bool:
    """
    Checks if a plain text password matches the hashed version in the DB.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) ->str:
    """
    Hashes a plain text password for safe storage in the database.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a cryptographically signed JSON Web Token (JWT).
    
    Args:
        data (dict): The payload to store inside the token (e.g., {"sub": "user_id_123"}).
        expires_delta (timedelta): How long until the token becomes invalid.
    """

    # Create a copy of the data so we don't mutate the original dictionary
    to_encode = data.copy()

    # Determine the exact expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add the expiration time to the JWT payload
    to_encode.update({"exp": expire})

    # Sign the token using our SECRET_KEY and the HS256 algorithm
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encode_jwt