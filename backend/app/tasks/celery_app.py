"""
Celery Application — Task queue configuration with Redis broker.
Stub for Sprint 1, fully implemented in Sprint 2.
"""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "formatguard",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.processing_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
    worker_prefetch_multiplier=1,  # One task at a time for document isolation
    task_always_eager=True,  # Bypass Redis since Docker is not available
)
