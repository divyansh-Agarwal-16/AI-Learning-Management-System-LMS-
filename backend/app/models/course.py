"""Course models module for the AI LMS database.

This module houses the SQLAlchemy configurations for courses,
lesson structures, dynamic player resources, and user enrollment linking tables.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, ForeignKey, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    """Course database model configuration.

    Attributes:
        id (str): Primary key text identifier (e.g. 'python-basics').
        title (str): Course name.
        description (str): Explanatory course context text details.
        difficulty (str): Categorization badge (e.g. Beginner, Intermediate).
        duration (str): Estimation metrics of workload completion (e.g. '5.5 hrs').
    """

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[str] = mapped_column(String(50), nullable=False)

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


class Lesson(Base):
    """Lesson database model configuration.

    Attributes:
        id (str): Primary key text identifier.
        course_id (str): Course foreign link.
        title (str): Name of the specific lesson.
        duration (str): Approximate duration of content.
        videoUrl (str): Optional resource stream location.
        pdfUrl (str): Optional textbook documentation location.
        order (int): Ordering number index for sorting.
    """

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
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


class Enrollment(Base):
    """Enrollment database model linking users and enrolled courses.

    Attributes:
        id (int): Primary key ID.
        user_id (int): Core user referencing key.
        course_id (str): Reference course key.
        enrolled_at (datetime): Timestamp tracking date.
    """

    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
