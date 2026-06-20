"""Database configuration module for the AI LMS backend.

This module initializes the asynchronous SQLAlchemy engine and session maker,
and establishes the declarative base class for all database models.

Relationships Diagram:
======================

  [User] 1 <---> 1 [UserProfile]
  [User] 1 <---> 1 [OnboardingData]
  [User] 1 <---> * [Enrollment] * <---> 1 [Course]
  [User] 1 <---> * [Submission] * <---> 1 [Quiz]
  [User] 1 <---> * [LessonProgress]
  [User] 1 <---> * [CourseProgress]
  [User] 1 <---> * [ChatHistory]
  
  [Course] 1 <---> * [Lesson]
  [Course] 1 <---> * [Enrollment]
  [Course] 1 <---> * [Quiz]
  [Course] 1 <---> * [ChatHistory]
  [Course] 1 <---> * [CourseProgress]
  
  [Lesson] 1 <---> * [LessonProgress]
  [Quiz] 1 <---> * [Question]
  [Quiz] 1 <---> * [Submission]
  [Question] 1 <---> * [Answer]
  [Submission] 1 <---> * [Answer]

ASCII Schema Diagram:
--------------------

       +---------------+       1 : 1       +---------------+
       | UserProfile   |<------------------| User          |
       +---------------+                   +---------------+
                                             |   |   |   |
                  +--------------------------+   |   |   +--------------------------+
                  |                              |   |                              |
                  v 1:*                          v   v 1:*                          v 1:*
       +---------------+                 +------------+                  +---------------+
       | ChatHistory   |                 | Enrollment |                  | LessonProgress|
       +---------------+                 +------------+                  +---------------+
           * : 1 |                           * : 1                               | * : 1
                 v                               v                               v
       +---------------+                 +------------+                  +---------------+
       | Course        |                 | Lesson     |                  | Lesson        |
       +---------------+                 +------------+                  +---------------+
         |   |   |   |
         |   |   |   +-----------------------+
         |   |   +-------------------+       |
         |   +-------------------+   |       v 1:*
         v 1:*                   v   v 1:* +----------------+
       +---------------+  +------------+   | CourseProgress |
       | ChatHistory   |  | Quiz       |   +----------------+
       +---------------+  +------------+
                            | 1:*  | 1:*
                            v      v
       +---------------+  +------------+
       | Question      |  | Submission |
       +---------------+  +------------+
           | 1:*             | 1:*
           v                 v
       +--------------------------------+
       | Answer                         |
       +--------------------------------+
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create database connection engine using asyncpg driver
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG and settings.APP_ENV == "development",
    future=True
)

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative database models."""
    pass


from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

class TimestampMixin:
    """Mixin adding created_at and updated_at timestamps to models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

