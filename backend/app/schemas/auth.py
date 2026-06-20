"""Auth schema definitions for authentication input and token validation.

This module houses validation schemas for user registration inputs, login
details, and JWT access/refresh token responses.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema validating email and password input credentials.

    Attributes:
        email (EmailStr): User registration email.
        password (str): Plain text password.
    """
    email: EmailStr
    password: str = Field(..., min_length=6, description="Plain text login password")


class SignupRequest(BaseModel):
    """Schema validating registration parameters.

    Attributes:
        email (EmailStr): Unique login email address.
        password (str): Plain text password constraints.
        full_name (str): The full name of the user.
    """
    email: EmailStr
    password: str = Field(..., min_length=6, description="Secure account password")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")


class TokenResponse(BaseModel):
    """Schema structure mapping returned JWT security credentials.

    Attributes:
        access_token (str): JWT signature validating session context.
        refresh_token (str): Long-lived signature to exchange expired access tokens.
        token_type (str): Token transport scheme. Defaults to Bearer.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
