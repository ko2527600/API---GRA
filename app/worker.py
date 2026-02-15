"""Celery worker entry point"""
from app.services.task_queue import celery_app
from app.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Starting Celery worker")
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=4",
        "--prefetch-multiplier=1",
    ])
