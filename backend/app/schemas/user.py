"""User schemas for validating profile data and onboarding details.

This module houses validation structures for reading user records, updating profile
fields, and processing onboarding survey responses.
"""

import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserProfileSchema(BaseModel):
    """Schema representing user profile details.

    Attributes:
        full_name (Optional[str]): Detailed display name.
        avatar_url (Optional[str]): Path link to uploaded display images.
        bio (Optional[str]): Narrative text biography.
    """
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

    model_config = {"from_attributes": True}


class OnboardingDataSchema(BaseModel):
    """Schema representing user onboarding preferences.

    Attributes:
        topic (Optional[str]): Primary study interest.
        level (Optional[str]): User skill level index.
        hours_per_week (float): Workload target.
    """
    topic: Optional[str] = None
    level: Optional[str] = None
    hours_per_week: float = 0.0

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """Schema validating final returned User payload context.

    Attributes:
        id (uuid.UUID): Primary User key ID.
        email (EmailStr): Login address.
        role (str): Authorized user privilege tier.
        is_active (bool): Active session lock flag.
        profile (Optional[UserProfileSchema]): Display information.
        onboarding (Optional[OnboardingDataSchema]): Custom preferences.
    """
    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    profile: Optional[UserProfileSchema] = None
    onboarding: Optional[OnboardingDataSchema] = None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """Schema validating updates sent to profile endpoints.

    Attributes:
        full_name (Optional[str]): Updated user name.
        bio (Optional[str]): Updated description.
        avatar_url (Optional[str]): New avatar image path.
    """
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=512)


class OnboardingRequest(BaseModel):
    """Schema validating selections sent to onboarding endpoints.

    Attributes:
        topic (str): Study topic.
        level (str): Self-reported skill level (Beginner, Intermediate, Advanced).
        hours_per_week (float): Allocated study hours.
    """
    topic: str = Field(..., description="Target discipline topic (e.g. Programming)")
    level: str = Field(..., description="Syllabus skill difficulty (Beginner, Intermediate, Advanced)")
    hours_per_week: float = Field(..., ge=0.0, le=168.0, description="Hours studied weekly")
