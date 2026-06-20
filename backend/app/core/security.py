"""Security and authentication helper module for the AI LMS backend.

This module provides operations for password hashing and verification
using bcrypt, as well as JWT token generation, signature validation,
and decryption for user authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings


def hash_password(password: str) -> str:
    """Hashes a plain text password using bcrypt.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        str: The decoded bcrypt string hash.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed bcrypt password.

    Args:
        plain_password (str): The plain-text password to verify.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates an access JWT token.

    Args:
        data (Dict[str, Any]): The payload data to encode inside the token.
        expires_delta (Optional[timedelta]): Custom token expiration delta.

    Returns:
        str: The signed JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a refresh JWT token.

    Args:
        data (Dict[str, Any]): The payload data to encode inside the token.
        expires_delta (Optional[timedelta]): Custom token expiration delta.

    Returns:
        str: The signed JWT refresh token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    """Decodes and validates a JWT token.

    Args:
        token (str): The JWT token string.
        is_refresh (bool): Decides whether to use the refresh token key or access key.

    Returns:
        Dict[str, Any]: The decoded payload.

    Raises:
        JWTError: If the signature is invalid or token type mismatch.
    """
    secret = settings.JWT_REFRESH_SECRET_KEY if is_refresh else settings.JWT_SECRET_KEY
    payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
    
    expected_type = "refresh" if is_refresh else "access"
    if payload.get("type") != expected_type:
        raise JWTError("Token type verification mismatch")
        
    return payload
