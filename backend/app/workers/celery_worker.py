"""
Celery worker configuration and task definitions.
Handles background audit execution, report generation, and data exports.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "lead_audit_pro",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_routes={
        "app.workers.tasks.run_audit": {"queue": "audits"},
        "app.workers.tasks.generate_report": {"queue": "reports"},
        "app.workers.tasks.run_export": {"queue": "exports"},
        "app.workers.tasks.run_discovery_search": {"queue": "discovery"},
        "app.workers.tasks.run_enrichment_job": {"queue": "enrichment"},
        "app.workers.tasks.run_lead_scoring_job": {"queue": "scoring"},
    },
    beat_schedule={
        "cleanup-expired-reports": {
            "task": "app.workers.tasks.cleanup_expired_reports",
            "schedule": 86400.0,  # daily
        },
        "retry-failed-audits": {
            "task": "app.workers.tasks.retry_failed_audits",
            "schedule": 3600.0,  # hourly
        },
    },
)

celery_app.autodiscover_tasks(["app.workers"])
