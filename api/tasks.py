from api.celery_app import celery_app

@celery_app.task(name='process_ticket_task')
def process_ticket_task(message: str):
    from src.agent.custom_agent import TechCorpAgent
    agent = TechCorpAgent()
    return agent.handle_message(message)
