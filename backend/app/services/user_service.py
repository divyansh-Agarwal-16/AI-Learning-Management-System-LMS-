"""User service module for the AI LMS backend.

This module houses operations for reading profile details, updating profile fields,
and storing user onboarding configurations.
"""

import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.user import User, UserProfile, OnboardingData
from app.schemas.user import UpdateProfileRequest, OnboardingRequest


class UserService:
    """User profile management and onboarding business operations."""

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Fetches a database User with profile and onboarding relations loaded.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Core user primary key ID.

        Returns:
            Optional[User]: User database object, or None if not found.
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None

        result = await db.execute(
            select(User)
            .where(User.id == user_id, User.is_deleted == False)
            .options(
                selectinload(User.profile),
                selectinload(User.onboarding)
            )
        )
        return result.scalars().first()

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: uuid.UUID,
        request: UpdateProfileRequest
    ) -> Optional[User]:
        """Modifies user profile fields.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Core user primary key ID.
            request (UpdateProfileRequest): Target modified fields.

        Returns:
            Optional[User]: The updated database User object.
        """
        user_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id

        # Verify user exists and not deleted
        user = await UserService.get_user_by_id(db, user_uuid)
        if not user:
            return None

        # Select target profile
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_uuid))
        profile = result.scalars().first()
        if not profile:
            # Create a profile if missing for some reason
            profile = UserProfile(user_id=user_uuid)
            db.add(profile)

        # Apply profile fields if provided in request
        if request.full_name is not None:
            profile.full_name = request.full_name
        if request.bio is not None:
            profile.bio = request.bio
        if request.avatar_url is not None:
            profile.avatar_url = request.avatar_url

        await db.commit()
        return await UserService.get_user_by_id(db, user_uuid)

    @staticmethod
    async def save_onboarding(
        db: AsyncSession,
        user_id: uuid.UUID,
        request: OnboardingRequest
    ) -> Optional[User]:
        """Saves user onboarding selections.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Core user primary key ID.
            request (OnboardingRequest): Onboarding selections.

        Returns:
            Optional[User]: The updated database User object.
        """
        user_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id

        # Verify user exists and not deleted
        user = await UserService.get_user_by_id(db, user_uuid)
        if not user:
            return None

        result = await db.execute(select(OnboardingData).where(OnboardingData.user_id == user_uuid))
        onboarding = result.scalars().first()
        if not onboarding:
            onboarding = OnboardingData(user_id=user_uuid)
            db.add(onboarding)

        onboarding.topic = request.topic
        onboarding.level = request.level
        onboarding.hours_per_week = request.hours_per_week

        await db.commit()
        return await UserService.get_user_by_id(db, user_uuid)
