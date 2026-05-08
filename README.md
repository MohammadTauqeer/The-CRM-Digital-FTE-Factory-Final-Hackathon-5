# CRM AI Agent - TechCorp FTE Factory

## Project Overview
This project is an AI-powered customer support agent for TechCorp. It uses the Gemini 1.5 Flash model to handle customer inquiries via multiple channels (Email, Web Form, WhatsApp). The system is built with a decoupled architecture, using a FastAPI backend to manage a PostgreSQL database and a Celery worker with Redis for asynchronous task processing.

The agent is capable of:
- Searching a knowledge base for information.
- Creating support tickets.
- Retrieving customer history.
- Escalating complex issues to human agents.
- Sending responses back to customers through the appropriate channel.

## Tech Stack
- **Frontend:** Next.js 14 (App Router, Tailwind CSS, TypeScript)
- **Backend API:** FastAPI (Python)
- **AI Model:** Google Gemini 1.5 Flash
- **Database:** PostgreSQL
- **Task Queue:** Celery with Redis broker/backend
- **Communication:** MCP (Model Context Protocol) for tool integration

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis
- Gemini API Key

### Installation
1. Clone the repository.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Database Setup
1. Create a PostgreSQL database named `crm_db`.
2. Run the schema script:
   ```bash
   psql -d crm_db -f database/schema.sql
   ```

### Configuration
1. Copy `.env.example` to `.env`.
   ```bash
   cp .env.example .env
   ```
2. Fill in your `GEMINI_API_KEY`, `DATABASE_URL`, and `REDIS_URL` in the `.env` file.

### Running the Application

Each component should be run in a separate terminal:

1. **Start Redis Server:**
   ```bash
   redis-server
   ```

2. **Start Celery Worker:**
   ```bash
   celery -A api.celery_app worker --loglevel=info
   ```

3. **Start FastAPI Backend:**
   ```bash
   uvicorn api.main:app --reload
   ```

4. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

The frontend will be available at `http://localhost:3000` and the API at `http://localhost:8000`.

## How to run with Docker Compose

To run the entire stack (API, Worker, Database, Redis, and Frontend) using Docker:

1. **Configure Environment Variables:**
   Ensure you have a `.env` file in the root directory with your `GEMINI_API_KEY`.
   ```bash
   GEMINI_API_KEY=your_actual_key_here
   ```

2. **Run Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the Application:**
   - **Frontend:** `http://localhost:3000`
   - **API:** `http://localhost:8000`
   - **Postgres:** `localhost:5432`
   - **Redis:** `localhost:6379`

## Kubernetes Deployment (Bonus)

Basic templates for Kubernetes are provided in the `k8s/` directory.

1. **Create Secrets:**
   ```bash
   kubectl create secret generic crm-secrets \
     --from-literal=database-url='postgresql://postgres:postgres@db-service:5432/crm_db' \
     --from-literal=gemini-api-key='your_api_key'
   ```

2. **Apply Manifests:**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```
