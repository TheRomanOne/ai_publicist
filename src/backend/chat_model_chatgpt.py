import os
from typing import List
from openai import OpenAI
from server.websocket_handler import log_message, log_error

system_prompt = """You're an AI assistant representing the user in technical job interviews. Use the context from their code to show off their skills.\n\n
RULES:\n
- Focus on what they BUILT and ACHIEVED, not just code description\n
- Highlight technical skills (like algorithms, frameworks, optimizations)\n
- Mention file names when relevant (like 'In engine.py, they...')\n
- Keep it brief but informative\n
- If asked about something not in their code, relate to what they have done\n\n

RESPONSE STYLE:\n
- Be conversational, a little bit of a storyteller, and enthusiastic, not formal\n
- Use bullet points for listing skills or features\n
- Point out impressive aspects (optimization, clean architecture, etc.)\n
- Use simple terms over complex jargon\n
- Add technical depth where it matters\n\n
- use "\\n" for new lines

Example:\n
Q: "Tell me about their game engine"\n
A: "In their game engine (engine.py, rendering.py), they built:\n
• A fast collision system using spatial partitioning\n
• Clean entity-component architecture for game objects\n
• Custom shader pipeline for realistic lighting\n
Their implementation shows strong systems design and optimization skills!"
"""



class ChatModelChatGPT:
    """OpenAI ChatGPT-based model wrapper."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Initialize the ChatGPT model.
        
        Args:
            api_key: OpenAI API key
            model: Model ID to use (defaults to gpt-3.5-turbo)
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)  # Pass API key correctly
        self.model = model
        print(f"Initialized ChatGPT model: {model}")

    def generate_response(self, message: str, context: List[str]) -> str:
        """Generate a response using ChatGPT.
        
        Args:
            message: User's question
            context: List of relevant code snippets
        
        Returns:
            Generated response
        """

        user_prompt = f"""
            Recruiter Question: {message}

            <Context>:
            {context}
            </Context>

            Respond based on the context and follow the system instructions for tone and style.
            """
        try:
            # Create system prompt

            # Generate response
            response = self.client.chat.completions.create(  # Corrected API call
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for factual responses
                max_tokens=500,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            resp = response.choices[0].message.content.strip()
            # Log the response
            log_message(f"ChatGPT generated response:\n{resp}")

        except Exception as e:
            # Extract the error message from the OpenAI error response
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    if 'error' in error_data and 'message' in error_data['error']:
                        error_msg = error_data['error']['message']
                except:
                    pass
            resp = f"Error: {error_msg}"
            log_error(f"Error generating response: {error_msg}")
        
        
        return resp
