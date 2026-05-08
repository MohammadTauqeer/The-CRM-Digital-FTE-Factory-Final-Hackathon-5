import os
import time
import json
import google.generativeai as genai
from dotenv import load_dotenv
import typing_extensions as typing
from src.agent.mcp_server import TechCorpMCPServer

# Load environment variables
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class TechCorpAgent:
    """
    A tool-enabled custom agent for TechCorp customer support.
    Integrates with TechCorpMCPServer to perform complex tasks via function calling.
    """
    
    def __init__(self, model_name="gemini-2.0-flash"):
        self.server = TechCorpMCPServer()
        
        # Define the tools available to the agent
        self.tools = [
            self.server.search_knowledge_base,
            self.server.create_ticket,
            self.server.get_customer_history,
            self.server.escalate_to_human,
            self.server.send_response
        ]
        
        # System instruction to enforce the workflow
        self.system_instruction = """
You are a senior customer support agent for TechCorp.
You have access to a set of tools to help you resolve customer inquiries.

WORKFLOW:
1. When a customer contacts you, FIRST check their history using 'get_customer_history' if a customer ID is provided.
2. THEN, search the knowledge base using 'search_knowledge_base' to find the most accurate information for their issue.
3. AFTER gathering all necessary information, use 'send_response' to provide the final answer to the customer.
4. If the issue is complex (billing, refunds, or high frustration), use 'escalate_to_human'.

IMPORTANT: Always follow this sequence. Do not skip steps.
Use 'create_ticket' if you need to track a new issue that cannot be resolved in one turn.
"""
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=self.tools,
            system_instruction=self.system_instruction
        )
        
        # Initialize chat session. Manual tool calling to allow for rate-limit throttling.
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)

    def handle_message(self, message: str):
        """
        Sends a message to the agent and returns the final response.
        Tool calls are handled manually with throttling to prevent 429 errors.
        """
        # Throttling before the initial model call
        time.sleep(2)
        response = self.chat.send_message(message)
        
        while True:
            # Check for function calls in the response
            if not (response.candidates and 
                    response.candidates[0].content.parts and 
                    response.candidates[0].content.parts[0].function_call):
                break
                
            tool_call = response.candidates[0].content.parts[0].function_call
            
            # Map tool names to functions
            tool_map = {
                "search_knowledge_base": self.server.search_knowledge_base,
                "create_ticket": self.server.create_ticket,
                "get_customer_history": self.server.get_customer_history,
                "escalate_to_human": self.server.escalate_to_human,
                "send_response": self.server.send_response
            }
            
            handler = tool_map.get(tool_call.name)
            if handler:
                result = handler(**tool_call.args)
                
                # Throttling before sending the tool response back to the model
                time.sleep(2)
                response = self.chat.send_message(
                    genai.types.Part.from_function_response(
                        name=tool_call.name,
                        response={'result': result}
                    )
                )
            else:
                break
                
        return response.text

if __name__ == "__main__":
    agent = TechCorpAgent()
    
    print("--- Custom Agent Tool-Enabled Simulation ---")
    
    # Simulation: A user asking about their previous tickets
    # This should trigger get_customer_history
    user_query = "Hi, I'm CUST-001. Can you tell me what happened with my previous tickets and how I can reset my password?"
    
    print(f"\n[User]: {user_query}")
    print("\n[Agent is processing and calling tools...]")
    
    try:
        response = agent.handle_message(user_query)
        
        print(f"\n[Final Agent Response]:\n{response}")
        
        # Inspect chat history to see tool calls (optional but good for verification)
        print("\n--- Tool Call History (Internal) ---")
        for content in agent.chat.history:
            for part in content.parts:
                if fn := part.function_call:
                    print(f"Tool Call: {fn.name}({fn.args})")
                if fr := part.function_response:
                    print(f"Tool Response: {fr.name} -> {fr.response}")
    except Exception as e:
        print(f"\n[Execution Error]: {e}")
        print("\nNote: If you see a 429 ResourceExhausted error, it means the API quota has been reached. The code structure is correct and ready for use once quota is available.")
