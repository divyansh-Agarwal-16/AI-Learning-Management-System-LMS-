"""Dependencies configuration module for the AI LMS backend.

This module houses injection dependencies for yielding active database
sessions and resolving/validating user contexts for protected routes.
"""

import uuid
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User

# OAuth2 Scheme mapping to authorization header bearer extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yields a database session context manager.

    Yields:
        AsyncGenerator[AsyncSession, None]: The database session context.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extracts and validates user session from auth JWT header.

    Args:
        token (str): JWT token.
        db (AsyncSession): Active database session.

    Returns:
        User: The authenticated database User object.

    Raises:
        HTTPException: 401 status if verification fails or user doesn't exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, is_refresh=False)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        uuid_user_id = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    # Query user database entry asynchronously
    result = await db.execute(select(User).where(User.id == uuid_user_id, User.is_deleted == False))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception

    return user
