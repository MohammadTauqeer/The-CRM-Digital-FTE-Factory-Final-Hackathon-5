import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def mcp_tool(func):
    """
    Simple decorator to mark a function as an MCP tool for simulation.
    In a real MCP implementation, this would register the function with the MCP server.
    """
    func._is_mcp_tool = True
    return func

class TechCorpMCPServer:
    """
    A simulated Model Context Protocol (MCP) server for TechCorp's customer support agent.
    Exposes agent capabilities as tools that can be invoked by an LLM.
    """
    
    def __init__(self, doc_path="context/product-docs.md"):
        self.doc_path = doc_path

    def get_db_connection(self):
        return psycopg2.connect(dbname='crm_db', user='postgres', password='postgres', host='127.0.0.1', port='5432')

    def _parse_customer_id(self, customer_id_str: str) -> int:
        """Helper to extract integer ID from string like 'CUST-001' or '1'"""
        if isinstance(customer_id_str, str) and customer_id_str.startswith("CUST-"):
            try:
                return int(customer_id_str.replace("CUST-", ""))
            except ValueError:
                pass
        try:
            return int(customer_id_str)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid customer ID format: {customer_id_str}")

    @mcp_tool
    def search_knowledge_base(self, query: str) -> str:
        """
        Searches the context/product-docs.md based on a query.
        Returns relevant sections of the documentation.
        """
        try:
            if not os.path.exists(self.doc_path):
                return "Knowledge base not found."
                
            with open(self.doc_path, "r") as f:
                content = f.read()
            
            # Simple keyword-based section search
            # Split by markdown headers
            sections = content.split("\n## ")
            results = []
            
            # Check the first section (usually the title)
            if query.lower() in sections[0].lower():
                results.append(sections[0])
                
            # Check subsequent sections
            for i in range(1, len(sections)):
                section_text = "## " + sections[i]
                if query.lower() in section_text.lower():
                    results.append(section_text)
            
            if not results:
                return f"No specific information found for '{query}' in the knowledge base."
            
            return "\n\n".join(results)
            
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"

    @mcp_tool
    def create_ticket(self, customer_id: str, issue: str, channel: str) -> str:
        """
        Creates a ticket in the database.
        """
        conn = None
        try:
            db_id = self._parse_customer_id(customer_id)
            conn = self.get_db_connection()
            with conn.cursor() as cur:
                # Truncate issue for subject, use full issue for message
                subject = (issue[:47] + '...') if len(issue) > 50 else issue
                cur.execute(
                    "INSERT INTO tickets (customer_id, channel, subject, message, status) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (db_id, channel, subject, issue, 'open')
                )
                ticket_id = cur.fetchone()[0]
                conn.commit()
                return f"SUCCESS: Ticket TKT-{ticket_id} created for customer CUST-{db_id} ({channel}). Issue: {issue}"
        except Exception as e:
            if conn:
                conn.rollback()
            return f"ERROR: Could not create ticket: {str(e)}"
        finally:
            if conn:
                conn.close()

    @mcp_tool
    def get_customer_history(self, customer_id: str) -> str:
        """
        Fetches past interactions for a specific customer from the database.
        """
        conn = None
        try:
            db_id = self._parse_customer_id(customer_id)
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, subject, status, created_at FROM tickets WHERE customer_id = %s ORDER BY created_at DESC",
                    (db_id,)
                )
                tickets = cur.fetchall()
                
                if not tickets:
                    return f"No previous interactions found for customer CUST-{db_id}."
                
                history_lines = []
                for t in tickets:
                    date_str = t['created_at'].strftime("%Y-%m-%d")
                    history_lines.append(f"{date_str}: {t['subject']} ({t['status']}).")
                
                return " ".join(history_lines)
        except Exception as e:
            return f"ERROR: Could not fetch customer history: {str(e)}"
        finally:
            if conn:
                conn.close()

    @mcp_tool
    def escalate_to_human(self, ticket_id: str, reason: str) -> str:
        """
        Simulates escalating a ticket to a human supervisor.
        Should be used for complex billing issues, refund requests, or angry customers.
        """
        return f"SUCCESS: Ticket {ticket_id} has been escalated to a human supervisor. Reason: {reason}"

    @mcp_tool
    def send_response(self, ticket_id: str, message: str) -> str:
        """
        Simulates sending a response to the customer.
        Final step in resolving or updating a ticket.
        """
        return f"SUCCESS: Response sent for {ticket_id}. Message summary: {message[:30]}..."

if __name__ == "__main__":
    # Note: These tests will fail if the database 'crm_db' is not running/accessible
    server = TechCorpMCPServer()
    
    print("--- Testing MCP Tools (Requires DB) ---")
    # We'll just print instructions as actual DB tests might fail in this environment
    print("Run these tools with a live PostgreSQL instance to verify database integration.")
