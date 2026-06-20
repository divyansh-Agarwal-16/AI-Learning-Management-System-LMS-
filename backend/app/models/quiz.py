"""Quiz models module for the AI LMS database.

This module houses the SQLAlchemy configurations for user practice quizzes,
individual questions with choice JSON fields, and submission metrics recording scores.
"""

from datetime import datetime, timezone
from typing import List, Optional, Any
from sqlalchemy import String, ForeignKey, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Quiz(Base):
    """Quiz database model holding quiz context properties.

    Attributes:
        id (int): Primary key ID.
        course_id (str): Course code link target.
        title (str): Title name of the quiz.
    """

    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
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


class Question(Base):
    """Question database model carrying prompt questions and choices.

    Attributes:
        id (int): Primary key ID.
        quiz_id (int): Core parent Quiz reference.
        text (str): Prompt question string text.
        options (Any): JSON serialized list array of text choices.
        correct_answer_idx (int): Zero-indexed indicator of the correct choice.
    """

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(String(512), nullable=False)
    options: Mapped[Any] = mapped_column(JSON, nullable=False)  # List[str] options
    correct_answer_idx: Mapped[int] = mapped_column(Integer, nullable=False)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan"
    )


class Submission(Base):
    """Submission database model wrapping grading summaries.

    Attributes:
        id (int): Primary key ID.
        user_id (int): Submitting student User ID.
        quiz_id (int): Target graded Quiz ID.
        score (int): Score index tracking total correct.
        total_questions (int): Count of total questions graded.
        submitted_at (datetime): Timestamp.
    """

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="submissions")
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="submissions")
    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="submission",
        cascade="all, delete-orphan"
    )


class Answer(Base):
    """Answer database model holding individual user choices.

    Attributes:
        id (int): Primary key ID.
        submission_id (int): Graded submission wrapper.
        question_id (int): Question ID context reference.
        selected_option_idx (int): Selected user choice index.
    """

    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_option_idx: Mapped[int] = mapped_column(Integer, nullable=False)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")
