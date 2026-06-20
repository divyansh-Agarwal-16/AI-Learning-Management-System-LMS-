"""Users router module for the AI LMS backend.

This module exposes endpoints for fetching the active user's profile details,
updating profile settings (avatar/bio/name), and submitting onboarding preferences.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.user import UserResponse, UpdateProfileRequest, OnboardingRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])
logger = structlog.get_logger()


@router.get("/profile", response_model=ApiResponse[UserResponse])
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches the authenticated user profile and onboarding settings.

    Args:
        current_user (User): The currently logged in database User.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[UserResponse]: Standardized user details response payload.
    """
    logger.info("user_profile_fetch", user_id=current_user.id)
    user = await UserService.get_user_by_id(db, current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return ApiResponse(
        success=True,
        data=UserResponse.model_validate(user),
        message="User profile fetched successfully"
    )


@router.put("/profile", response_model=ApiResponse[UserResponse])
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates the authenticated user's profile display details.

    Args:
        request (UpdateProfileRequest): Updated profile parameters.
        current_user (User): Currently logged in database User.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[UserResponse]: Standardized updated user details response.
    """
    logger.info("user_profile_update_attempt", user_id=current_user.id)
    user = await UserService.update_profile(db, current_user.id, request)
    logger.info("user_profile_update_success", user_id=current_user.id)
    return ApiResponse(
        success=True,
        data=UserResponse.model_validate(user),
        message="User profile updated successfully"
    )


@router.post("/onboarding", response_model=ApiResponse[UserResponse])
async def onboarding(
    request: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Saves user onboarding course interest selections.

    Args:
        request (OnboardingRequest): Onboarding selections.
        current_user (User): Currently logged in database User.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[UserResponse]: Standardized user details carrying onboarding records.
    """
    logger.info("user_onboarding_attempt", user_id=current_user.id)
    user = await UserService.save_onboarding(db, current_user.id, request)
    logger.info("user_onboarding_success", user_id=current_user.id)
    return ApiResponse(
        success=True,
        data=UserResponse.model_validate(user),
        message="Onboarding completed successfully"
    )
