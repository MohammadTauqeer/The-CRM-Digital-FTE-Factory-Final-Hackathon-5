#!/bin/bash
# Run Celery Worker in background
celery -A api.celery_app worker --loglevel=info &
# Run FastAPI in foreground
gunicorn -w 2 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:${PORT:-8000}
