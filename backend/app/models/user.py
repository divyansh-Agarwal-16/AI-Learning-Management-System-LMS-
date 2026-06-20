"""User models module for the AI LMS database.

This module houses the SQLAlchemy schema configurations for User credentials,
detailed profile bios/avatars, and onboarding selections.
"""

from typing import List, Optional
from sqlalchemy import String, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """User database model holding core authentication and role details.

    Attributes:
        id (int): Primary key ID.
        email (str): Unique, indexed login email address.
        hashed_password (str): Hash key string of password.
        is_active (bool): User active status.
        role (str): Role designation (e.g., student, admin).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    role: Mapped[str] = mapped_column(String(50), default="student")

    # One-to-One Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    onboarding: Mapped[Optional["OnboardingData"]] = relationship(
        "OnboardingData",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # One-to-Many Relationships
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    lesson_progresses: Mapped[List["LessonProgress"]] = relationship(
        "LessonProgress",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    course_progresses: Mapped[List["CourseProgress"]] = relationship(
        "CourseProgress",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    chat_histories: Mapped[List["ChatHistory"]] = relationship(
        "ChatHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class UserProfile(Base):
    """UserProfile database model storing user profile customization.

    Attributes:
        id (int): Primary key ID.
        user_id (int): Foreign key referencing core User.
        full_name (str): The user's name.
        avatar_url (str): Storage path link to uploaded user avatar images.
        bio (str): Custom bio writeup.
    """

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class OnboardingData(Base):
    """OnboardingData database model holding onboarding preferences.

    Attributes:
        id (int): Primary key ID.
        user_id (int): Foreign key referencing core User.
        topic (str): Primary education topic selection.
        level (str): Self-selected skill level capability.
        hours_per_week (float): Targeted workload timing settings.
    """

    __tablename__ = "onboarding_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hours_per_week: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped["User"] = relationship("User", back_populates="onboarding")
