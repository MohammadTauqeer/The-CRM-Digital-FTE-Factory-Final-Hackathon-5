from dotenv import load_dotenv

# Load environment variables at the very top
load_dotenv()

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Custom CRM API")

# Ensure GEMINI_API_KEY is available
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://crm-fte-frontend.onrender.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection helper
def get_db_connection():
    import psycopg2
    db_url = os.getenv("DATABASE_URL", "dbname='crm_db' user='postgres' password='postgres' host='127.0.0.1' port='5432'")
    if os.getenv("RENDER"):
        print(f"Connecting to DB: {db_url.split('@')[-1] if '@' in db_url else 'local'}")
    return psycopg2.connect(db_url)

# Pydantic models
class CustomerBase(BaseModel):
    email: EmailStr
    name: str

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TicketBase(BaseModel):
    customer_id: int
    channel: str
    subject: str
    message: str
    status: str = "open"

class TicketCreate(TicketBase):
    pass

class Ticket(TicketBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SupportRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    channel: str
    message: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Custom CRM API"}

@app.post("/customers/", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    conn = get_db_connection()
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO customers (email, name) VALUES (%s, %s) RETURNING id, email, name, created_at",
                (customer.email, customer.name)
            )
            new_customer = cur.fetchone()
            conn.commit()
            return new_customer
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/customers/", response_model=List[Customer])
async def read_customers():
    conn = get_db_connection()
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, email, name, created_at FROM customers")
            return cur.fetchall()
    finally:
        conn.close()

@app.post("/tickets/", response_model=Ticket)
async def create_ticket(ticket: TicketCreate):
    conn = get_db_connection()
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if customer exists
            cur.execute("SELECT id FROM customers WHERE id = %s", (ticket.customer_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Customer not found")
            
            cur.execute(
                "INSERT INTO tickets (customer_id, channel, subject, message, status) VALUES (%s, %s, %s, %s, %s) RETURNING id, customer_id, channel, subject, message, status, created_at",
                (ticket.customer_id, ticket.channel, ticket.subject, ticket.message, ticket.status)
            )
            new_ticket = cur.fetchone()
            conn.commit()
            return new_ticket
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/tickets/", response_model=List[Ticket])
async def read_tickets(customer_id: Optional[int] = None, status: Optional[str] = None):
    conn = get_db_connection()
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = "SELECT id, customer_id, channel, subject, message, status, created_at FROM tickets WHERE 1=1"
            params = []
            if customer_id:
                query += " AND customer_id = %s"
                params.append(customer_id)
            if status:
                query += " AND status = %s"
                params.append(status)
            
            cur.execute(query, tuple(params))
            return cur.fetchall()
    finally:
        conn.close()

@app.patch("/tickets/{ticket_id}", response_model=Ticket)
async def update_ticket_status(ticket_id: int, status: str):
    conn = get_db_connection()
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE tickets SET status = %s WHERE id = %s RETURNING id, customer_id, channel, subject, message, status, created_at",
                (status, ticket_id)
            )
            updated_ticket = cur.fetchone()
            if not updated_ticket:
                raise HTTPException(status_code=404, detail="Ticket not found")
            conn.commit()
            return updated_ticket
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/customers/search", response_model=List[Customer])
async def search_customers(email: str):
    conn = get_db_connection()
    try:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, email, name, created_at FROM customers WHERE email ILIKE %s",
                (f"%{email}%",)
            )
            return cur.fetchall()
    finally:
        conn.close()

@app.post("/support/submit")
async def submit_support_request(request: SupportRequest):
    # Push the ticket processing to the background
    from api.tasks import process_ticket_task
    task = process_ticket_task.delay(request.message)
    return {
        "status": "queued",
        "ticket_created": True,
        "task_id": task.id,
        "message": "Your request is being processed."
    }

@app.get("/support/status/{task_id}")
async def get_task_status(task_id: str):
    from api.celery_app import celery_app
    task = celery_app.AsyncResult(task_id)
    if task.state in ['PENDING', 'STARTED']:
        return {"status": "processing"}
    elif task.state == 'SUCCESS':
        return {"status": "success", "agent_response": task.result}
    elif task.state == 'FAILURE':
        return {"status": "failed"}
    else:
        return {"status": task.state.lower()}
