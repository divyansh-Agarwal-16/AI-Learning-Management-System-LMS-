"""Quiz models module for the AI LMS database.

This module houses the SQLAlchemy configurations for user practice quizzes,
individual questions with choice JSON fields, and submission metrics recording scores.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import String, ForeignKey, Integer, DateTime, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Quiz(Base, TimestampMixin):
    """Quiz database model holding quiz context properties.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        course_id (uuid.UUID): Course code link target.
        title (str): Title name of the quiz.
    """

    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="quizzes")
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan"
    )
    submissions: Mapped[List["Submission"]] = relationship(
        "Submission",
        back_populates="quiz",
        cascade="all, delete-orphan"
    )


class Question(Base, TimestampMixin):
    """Question database model carrying prompt questions and choices.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        quiz_id (uuid.UUID): Core parent Quiz reference.
        text (str): Prompt question string text.
        options (Any): JSON serialized list array of text choices.
        correct_answer_idx (int): Zero-indexed indicator of the correct choice.
    """

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    options: Mapped[Any] = mapped_column(JSON, nullable=False)  # List[str] options
    correct_answer_idx: Mapped[int] = mapped_column(Integer, nullable=False)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan"
    )


class Submission(Base, TimestampMixin):
    """Submission database model wrapping grading summaries.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        user_id (uuid.UUID): Submitting student User ID.
        quiz_id (uuid.UUID): Target graded Quiz ID.
        score (int): Score index tracking total correct.
        total_questions (int): Count of total questions graded.
        submitted_at (datetime): Timestamp.
    """

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="submissions")
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="submissions")
    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="submission",
        cascade="all, delete-orphan"
    )


class Answer(Base, TimestampMixin):
    """Answer database model holding individual user choices.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        submission_id (uuid.UUID): Graded submission wrapper.
        question_id (uuid.UUID): Question ID context reference.
        selected_option_idx (int): Selected user choice index.
    """

    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_idx: Mapped[int] = mapped_column(Integer, nullable=False)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")
