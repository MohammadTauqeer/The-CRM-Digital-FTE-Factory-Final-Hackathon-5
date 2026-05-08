import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import typing_extensions as typing

# Load environment variables (API keys, etc.)
load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Define the structured output schema
class SupportResponse(typing.TypedDict):
    response: str
    escalate: bool

def load_knowledge_base(path="context/product-docs.md"):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Knowledge base not found."

def generate_response(message: str, channel: str, history: list = None):
    if history is None:
        history = []
        
    knowledge_base = load_knowledge_base()
    
    # Channel-specific tone/formatting instructions
    channel_instructions = {
        "email": "Respond in a professional email format. Include a subject line at the top, followed by a formal greeting and closing.",
        "whatsapp": "Respond in a friendly, concise manner. Use bullet points if helpful, and keep it brief as it's a chat interface.",
        "web_form": "Respond clearly and directly. Provide a summary of the solution and any next steps."
    }
    
    instruction = channel_instructions.get(channel, "Respond professionally.")

    system_prompt = f"""
You are a helpful customer support agent for TechCorp. 
Use the following knowledge base to answer the customer's inquiry accurately.

KNOWLEDGE BASE:
{knowledge_base}

CHANNEL: {channel}
INSTRUCTIONS: {instruction}

Set escalate to true ONLY if the user asks for a refund, mentions a billing error, or sounds angry.
"""

    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=system_prompt
    )
    
    # Start a chat session with the provided history
    chat = model.start_chat(history=history)
    
    response = chat.send_message(
        message,
        generation_config=genai.types.GenerationConfig(
            temperature=0,
            # We want the model to return JSON
            response_mime_type="application/json",
            response_schema=SupportResponse
        )
    )
    
    return response.text

if __name__ == "__main__":
    try:
        with open("context/sample-tickets.json", "r") as f:
            tickets = json.load(f)
        
        # Simulate a conversation for the first ticket (TKT-001)
        ticket = tickets[0]
        history = []
        
        print(f"--- Conversation Simulation (Ticket: {ticket['id']}) ---")
        
        # Turn 1
        print(f"\n[User]: {ticket['message']}")
        raw_reply_1 = generate_response(ticket['message'], ticket['channel'], history)
        reply_data_1 = json.loads(raw_reply_1)
        print(f"[Agent]: {reply_data_1['response']}")
        print(f"Escalated: {'Yes' if reply_data_1['escalate'] else 'No'}")
        
        # Manually update history for the next turn
        history.append({"role": "user", "parts": [ticket['message']]})
        history.append({"role": "model", "parts": [raw_reply_1]})
        
        # Turn 2
        follow_up = "That makes sense. What are the specific CSV columns I need?"
        print(f"\n[User]: {follow_up}")
        raw_reply_2 = generate_response(follow_up, ticket['channel'], history)
        reply_data_2 = json.loads(raw_reply_2)
        print(f"[Agent]: {reply_data_2['response']}")
        print(f"Escalated: {'Yes' if reply_data_2['escalate'] else 'No'}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
