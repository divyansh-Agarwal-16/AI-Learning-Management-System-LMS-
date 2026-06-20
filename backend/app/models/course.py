"""Course models module for the AI LMS database.

This module houses the SQLAlchemy configurations for courses,
lesson structures, dynamic player resources, and user enrollment linking tables.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, ForeignKey, Text, Integer, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Course(Base, TimestampMixin):
    """Course database model configuration.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        title (str): Course name.
        description (str): Explanatory course context text details.
        difficulty (str): Categorization badge (e.g. Beginner, Intermediate).
        duration (str): Estimation metrics of workload completion (e.g. '5.5 hrs').
        is_deleted (bool): Soft delete flag.
    """

    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[str] = mapped_column(String(50), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    # Relationships
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.order"
    )
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    quizzes: Mapped[List["Quiz"]] = relationship(
        "Quiz",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    chat_histories: Mapped[List["ChatHistory"]] = relationship(
        "ChatHistory",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    course_progresses: Mapped[List["CourseProgress"]] = relationship(
        "CourseProgress",
        back_populates="course",
        cascade="all, delete-orphan"
    )


class Lesson(Base, TimestampMixin):
    """Lesson database model configuration.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        course_id (uuid.UUID): Course foreign link.
        title (str): Name of the specific lesson.
        duration (str): Approximate duration of content.
        videoUrl (str): Optional resource stream location.
        pdfUrl (str): Optional textbook documentation location.
        order (int): Ordering number index for sorting.
    """

    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[str] = mapped_column(String(50), nullable=False)
    videoUrl: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    pdfUrl: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
    progresses: Mapped[List["LessonProgress"]] = relationship(
        "LessonProgress",
        back_populates="lesson",
        cascade="all, delete-orphan"
    )


class Enrollment(Base, TimestampMixin):
    """Enrollment database model linking users and enrolled courses.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        user_id (uuid.UUID): Core user referencing key.
        course_id (uuid.UUID): Reference course key.
        enrolled_at (datetime): Timestamp tracking date.
    """

    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
