"""Alembic migration environment script.

Configures database connections and model metadata for schema autogeneration.
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Load configurations and Declarative Base metadata
from app.core.config import settings
from app.core.database import Base

# Import all database models to ensure registration on Base.metadata for autogenerate
from app.models.user import User, UserProfile, OnboardingData
from app.models.course import Course, Lesson, Enrollment
from app.models.quiz import Quiz, Question, Submission, Answer
from app.models.progress import LessonProgress, CourseProgress
from app.models.ai_logs import AIUsageLog, ChatHistory

config = context.config

# Setup standard logger configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Runs migrations in 'offline' mode.

    Configures the context with just a URL and not an engine.
    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Executes migrations sync context on an active connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Runs migrations in 'online' mode.

    Creates an AsyncEngine and associates a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
