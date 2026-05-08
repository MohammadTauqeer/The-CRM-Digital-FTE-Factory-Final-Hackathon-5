import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    'crm_tasks',
    broker=redis_url,
    backend=redis_url,
    include=['api.tasks']
)
