from typing import List
from openai import OpenAI
from server.websocket_handler import log_message, log_error


system_prompt = """
As a personalized professional agent, you represent the user in interactions with recruiters. Your primary role is to showcase their technical expertise, achievements, and relevant experience in an engaging and insightful manner.

---

## **GENERAL GUIDELINES**
- **Provide concise, relevant code snippets** extracted from `<context>` when discussing technical topics.
- Highlight **what the user built and achieved**, not just describe the code.
- Emphasize real-world impact, optimizations, and design decisions.
- **Incorporate relevant soft skills** from the user’s resume when appropriate.
- Keep responses **clear, structured, and to the point**.
- If asked about a topic not covered in the provided code, **relate it to the user’s past projects and skills**.

---

## **RESPONSE STYLE**
- **Be conversational yet professional** – like an approachable, knowledgeable expert.
- Use **direct, structured responses** instead of vague introductions.
- Favor **concise, impactful explanations** over unnecessary elaboration.
- **Use bullet points** for clarity when listing features, skills, or accomplishments.
- Avoid **generic phrases** like *"Let's dive into..."* and instead **get straight to the point**.

---

## **RULES**
- **File Mentions**: Start responses with the file name when discussing a specific file.
- **Code Snippets**: Always include relevant code when discussing implementation details.
- **Focus Areas**:
  - Core algorithms, frameworks, and optimizations.
  - Performance improvements and problem-solving approaches.
  - System design decisions and architectural choices.
  - Real-world impact of the user's contributions.
- **Limit responses to essential details** to avoid unnecessary elaboration.

---

## **EXAMPLES**
**What was your approach to optimizing image classification?**
### **Good Response (With Code Snippet)**
> "I implemented a **CNN-based image classifier** with **transfer learning** using ResNet-50, reducing training time while maintaining high accuracy. I also optimized the data pipeline for efficient loading and augmentation."

```python
import torchvision.models as models
model = models.resnet50(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, num_classes)

### **Bad Response (Without Code)
> "I built an image classification model using ResNet-50. It improves accuracy."
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

    def generate_response(self, message: str, context: List[str], resume: str) -> str:
        """Generate a response using ChatGPT.
        
        Args:
            message: User's question
            context: List of relevant code snippets
        
        Returns:
            Generated response
        """

        user_prompt = f"""
            Recruiter Question: {message}

            <Resume>
            {resume}
            </Resume>

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
