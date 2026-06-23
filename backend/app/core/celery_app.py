"""Celery application configuration for background tasks routing."""
import os
from celery import Celery

# Load Redis credentials URL from environment configurations
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ai_lms_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="app.core.celery_app.verify_connection")
def verify_connection():
    """Simple verification task to confirm worker connectivity."""
    return "Celery background worker is connected and healthy."
