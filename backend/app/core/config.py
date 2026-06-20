"""Configuration settings module for the AI LMS backend.

This module uses pydantic-settings to validate environment variables
and load configurations from the environment or .env files.
"""

import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings class validating variables from environment and .env files.

    Attributes:
        APP_NAME (str): Name of the application.
        APP_ENV (str): Environment stage (e.g. production, staging, development).
        DEBUG (bool): Debug mode flag.
        DATABASE_URL (str): Connection string for the PostgreSQL database.
        JWT_SECRET_KEY (str): Secret signature key for access tokens.
        JWT_REFRESH_SECRET_KEY (str): Secret signature key for refresh tokens.
        ALGORITHM (str): JWT signature algorithm.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Lifetime duration of access tokens.
        REFRESH_TOKEN_EXPIRE_DAYS (int): Lifetime duration of refresh tokens.
        OPENAI_API_KEY (str): API key for OpenAI LLM interface.
    """

    APP_NAME: str = "AI LMS Backend API"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/ailms")

    # Security
    JWT_SECRET_KEY: str = Field(default="fallback-secret-key-at-least-32-chars-long-change-in-prod")
    JWT_REFRESH_SECRET_KEY: str = Field(default="fallback-refresh-secret-key-at-least-32-chars-long-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI Configurations
    OPENAI_API_KEY: str = "mock-key-for-testing"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
