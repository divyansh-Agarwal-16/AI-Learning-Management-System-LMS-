"""AI Logs models module for the AI LMS database.

This module houses the SQLAlchemy configurations for logging AI API consumption
statistics and maintaining context history logs for student chats with the AI tutor.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, Integer, DateTime, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class AIUsageLog(Base, TimestampMixin):
    """AIUsageLog database model recording LLM service costs.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        user_id (uuid.UUID): Core user referencing key.
        action (str): Specific action triggering LLM calls (e.g. 'quiz_gen', 'chat').
        tokens_used (int): Overall payload size metrics.
        latency_ms (int): Processing duration metrics in milliseconds.
    """

    __tablename__ = "ai_usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)


class ChatHistory(Base, TimestampMixin):
    """ChatHistory database model saving student-tutor chat records.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        user_id (uuid.UUID): Core User reference ID.
        course_id (uuid.UUID): Core Course reference UUID.
        sender (str): Message source (e.g. user, assistant).
        message (str): Text content.
    """

    __tablename__ = "chat_histories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    sender: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="chat_histories")
    course: Mapped["Course"] = relationship("Course", back_populates="chat_histories")
