"""Authentication service module for the AI LMS backend.

This module houses business transactions for user registration, credentials
validation, and JWT access/refresh token exchanges.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User, UserProfile, OnboardingData
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse


class AuthService:
    """Authentication and session management business operations."""

    @staticmethod
    async def signup_user(db: AsyncSession, request: SignupRequest) -> Optional[User]:
        """Registers a new User inside the database with empty profiles.

        Args:
            db (AsyncSession): Active database session.
            request (SignupRequest): Signup credentials.

        Returns:
            Optional[User]: The created database User, or None if email exists.
        """
        # Validate unique email constraint
        result = await db.execute(select(User).where(User.email == request.email))
        existing_user = result.scalars().first()
        if existing_user:
            return None

        # Create user record
        hashed = hash_password(request.password)
        new_user = User(
            email=request.email,
            hashed_password=hashed,
            role="student"
        )
        db.add(new_user)
        await db.flush()  # Extract user id before child schemas are attached

        # Create default profile and onboarding data objects
        new_profile = UserProfile(
            user_id=new_user.id,
            full_name=request.full_name
        )
        new_onboarding = OnboardingData(
            user_id=new_user.id
        )
        db.add(new_profile)
        db.add(new_onboarding)
        
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, request: LoginRequest) -> Optional[User]:
        """Authenticates user login credentials.

        Args:
            db (AsyncSession): Active database session.
            request (LoginRequest): Input login credentials.

        Returns:
            Optional[User]: The authenticated database User object, or None if invalid.
        """
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalars().first()
        if not user:
            return None

        if not verify_password(request.password, user.hashed_password):
            return None

        return user

    @staticmethod
    def generate_auth_tokens(user: User) -> TokenResponse:
        """Generates standard access and refresh JWT token payloads for a User session.

        Args:
            user (User): The target authenticated User.

        Returns:
            TokenResponse: The container holding the generated tokens.
        """
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        access = create_access_token(data=token_data)
        refresh = create_refresh_token(data=token_data)
        return TokenResponse(access_token=access, refresh_token=refresh)

    @staticmethod
    async def refresh_user_token(db: AsyncSession, refresh_token: str) -> Optional[TokenResponse]:
        """Exchanges a valid refresh token for a brand new set of access/refresh tokens.

        Args:
            db (AsyncSession): Active database session.
            refresh_token (str): The refresh JWT token.

        Returns:
            Optional[TokenResponse]: The fresh token payload, or None if invalid.
        """
        try:
            payload = decode_token(refresh_token, is_refresh=True)
            user_id = payload.get("sub")
            if not user_id:
                return None
        except JWTError:
            return None

        # Verify user still exists in database
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalars().first()
        if not user or not user.is_active:
            return None

        # Generate fresh token pairs
        return AuthService.generate_auth_tokens(user)
