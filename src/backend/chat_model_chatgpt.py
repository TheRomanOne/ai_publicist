from typing import List
from openai import OpenAI
from server.websocket_handler import log_message, log_error
import re
from prompt import get_user_prompt, get_system_prompt



class ChatModelChatGPT:
    """OpenAI ChatGPT-based model wrapper."""
    
    def __init__(self, api_key: str, model: str, user_name: str):
        """Initialize the ChatGPT model.
        
        Args:
            api_key: OpenAI API key
            model: Model ID to use
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = get_system_prompt(user_name)

        print(f"Initialized ChatGPT model: {model}")

    def generate_response(self, message: str, context: List[str], resume: str, chat_history: str = "") -> dict:
        """Generate a response using ChatGPT."""
        
        user_prompt = get_user_prompt(message, resume, context, chat_history)

        try:
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for factual responses
                max_tokens=500,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            raw_content = response.choices[0].message.content.strip()
            
            # Extract summary using regex
            summary_match = re.search(r'<summary>(.*?)</summary>', raw_content, re.DOTALL | re.IGNORECASE)
            summary = summary_match.group(1).strip() if summary_match else ""
            
            # Remove summary from the response text
            # cleaned_content = re.sub(r'<summary>.*?</summary>', '', raw_content, flags=re.DOTALL | re.IGNORECASE).strip()
            cleaned_content = raw_content
            
            # Log the response and summary
            log_message(f"ChatGPT generated response:\n{cleaned_content}")
            log_message(f"Extracted summary:\n{summary}")
            
            return {
                "content": cleaned_content, 
                "summary": summary
            }

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
            
            return {
                "content": resp,
                "summary": ""
            }
