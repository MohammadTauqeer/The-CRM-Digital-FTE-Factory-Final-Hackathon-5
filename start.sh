#!/bin/bash
# Run Celery Worker in background
celery -A api.celery_app worker --loglevel=info --concurrency=1 --pool=solo &
# Run FastAPI in foreground
gunicorn -w 1 --worker-main-process-name "crm-api" -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:${PORT:-8000}
