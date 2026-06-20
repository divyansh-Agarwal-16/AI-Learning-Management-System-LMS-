"""AI Logs models module for the AI LMS database.

This module houses the SQLAlchemy configurations for logging AI API consumption
statistics and maintaining context history logs for student chats with the AI tutor.
"""

from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AIUsageLog(Base):
    """AIUsageLog database model recording LLM service costs.

    Attributes:
        id (int): Primary key ID.
        user_id (int): Core user referencing key.
        action (str): Specific action triggering LLM calls (e.g. 'quiz_gen', 'chat').
        tokens_used (int): Overall payload size metrics.
        latency_ms (int): Processing duration metrics in milliseconds.
        timestamp (datetime): Log execution time.
    """

    __tablename__ = "ai_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


class ChatHistory(Base):
    """ChatHistory database model saving student-tutor chat records.

    Attributes:
        id (int): Primary key ID.
        user_id (int): Core User reference ID.
        course_id (str): Core Course reference code.
        sender (str): Message source (e.g. user, assistant).
        message (str): Text content.
        timestamp (datetime): Timestamp.
    """

    __tablename__ = "chat_histories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    sender: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship("User", back_populates="chat_histories")
    course: Mapped["Course"] = relationship("Course", back_populates="chat_histories")
