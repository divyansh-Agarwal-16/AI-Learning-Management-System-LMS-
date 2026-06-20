"""Authentication router module for the AI LMS backend.

This module exposes endpoints for user registration, user login validation,
refreshing JWT tokens, and initiating password resets.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.base import ApiResponse
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = structlog.get_logger()


@router.post("/signup", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Registers a new student user in the database.

    Args:
        request (SignupRequest): Signup parameters.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[UserResponse]: Standardized signup response payload.
    """
    logger.info("user_signup_attempt", email=request.email)
    user = await AuthService.signup_user(db, request)
    if not user:
        logger.warning("user_signup_failed_email_exists", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    logger.info("user_signup_success", email=user.email, user_id=user.id)
    return ApiResponse(
        success=True,
        data=UserResponse.model_validate(user),
        message="User registered successfully"
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates a user via JSON payload and returns access/refresh JWT tokens.

    Args:
        request (LoginRequest): Input login credentials.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[TokenResponse]: Standardized login response carrying JWTs.
    """
    logger.info("user_login_attempt", email=request.email)
    user = await AuthService.authenticate_user(db, request)
    if not user:
        logger.warning("user_login_failed_invalid_credentials", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    tokens = AuthService.generate_auth_tokens(user)
    logger.info("user_login_success", email=user.email, user_id=user.id)
    return ApiResponse(
        success=True,
        data=tokens,
        message="Login successful"
    )


@router.post("/login/swagger", include_in_schema=False)
async def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Fallback endpoint for Swagger UI login compatibility."""
    request = LoginRequest(email=form_data.username, password=form_data.password)
    user = await AuthService.authenticate_user(db, request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    tokens = AuthService.generate_auth_tokens(user)
    return {
        "access_token": tokens.access_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Refreshes an expired session using a refresh token.

    Args:
        refresh_token (str): Valid refresh JWT token.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[TokenResponse]: Standardized response carrying new tokens.
    """
    logger.info("token_refresh_attempt")
    tokens = await AuthService.refresh_user_token(db, refresh_token)
    if not tokens:
        logger.warning("token_refresh_failed_invalid_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    logger.info("token_refresh_success")
    return ApiResponse(
        success=True,
        data=tokens,
        message="Tokens refreshed successfully"
    )


@router.post("/forgot-password", response_model=ApiResponse[None])
async def forgot_password(email: str, db: AsyncSession = Depends(get_db)):
    """Dispatches a mock password reset request notification.

    Args:
        email (str): Registered login email address.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[None]: Standardized empty response indicating reset initiation.
    """
    logger.info("password_reset_requested", email=email)
    # Simulated password recovery email check (mocked transaction)
    return ApiResponse(
        success=True,
        data=None,
        message="If the email exists, a password reset link has been sent."
    )
