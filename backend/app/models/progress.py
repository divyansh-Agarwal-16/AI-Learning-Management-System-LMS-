"""Progress models module for the AI LMS database.

This module houses the SQLAlchemy configurations for tracking user study progress,
lesson completion toggles, and overall course completion percentages.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, Integer, Boolean, Float, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class LessonProgress(Base, TimestampMixin):
    """LessonProgress database model tracking individual lesson milestones.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        user_id (uuid.UUID): Student User ID.
        lesson_id (uuid.UUID): Target lesson code.
        completed (bool): Completion state status.
        time_spent (int): Duration spent on lesson resource (in seconds).
    """

    __tablename__ = "lesson_progresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    time_spent: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User", back_populates="lesson_progresses")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="progresses")


class CourseProgress(Base, TimestampMixin):
    """CourseProgress database model tracking cumulative course milestones.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        user_id (uuid.UUID): Student User ID.
        course_id (uuid.UUID): Course code referencing key.
        percentage (float): Cumulative calculated percentage (0.0 to 100.0).
        status (str): Running status (not_started, in_progress, completed).
    """

    __tablename__ = "course_progresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="not_started")

    user: Mapped["User"] = relationship("User", back_populates="course_progresses")
    course: Mapped["Course"] = relationship("Course", back_populates="course_progresses")
