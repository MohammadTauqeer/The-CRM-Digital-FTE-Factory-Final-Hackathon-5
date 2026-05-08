from api.celery_app import celery_app
from src.agent.custom_agent import TechCorpAgent

@celery_app.task(name='process_ticket_task')
def process_ticket_task(message: str):
    agent = TechCorpAgent()
    return agent.handle_message(message)
