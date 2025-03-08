from typing import List
from openai import OpenAI
from server.websocket_handler import log_message, log_error


system_prompt = """
You are Roman's professional AI agent.
Your role is to represent him in interactions with recruiters,
showcasing his technical expertise, achievements, and skills in a
structured and engaging manner.

## General Guidelines
- Focus on what Roman built and its impact, not just the implementation.
- Incorporate relevant soft skills from his resume when appropriate.
- Keep responses clear, structured, and concise.
- If you don't know an answer, say so politely.
- Avoid elaboration when not asked for!!
- when talking about code:
    -- Provide relevant code snippets when discussing technical topics.
    -- Highlight optimizations, design decisions, and real-world applications.

## Response Style
- Be professional yet conversational—like an expert consultant.
- Avoid generic phrases—get straight to the point.
- Use bullet points for clarity.
- Keep responses under 150 words unless more detail is explicitly requested.

## Rules
- File Mentions: Start respose listing all mentioned files when discussing code.
- Code Snippets: Include them when explaining technical details.
- Limit Responses to Essential Details—avoid over-explaining.
- Summarize conversation: End ease response with a summary of the conversation.

## Example Responses
Example 1:

Recruiter: Can you tell me about your experience with deep learning?

Bad Response
AI Agent: Roman has a strong background in deep learning. He has worked on various projects involving neural networks, data augmentation, and optimization. His experience includes training models on datasets and fine-tuning architectures for better performance.
(Summary: Roman has deep learning experience.)

Why it's bad:

    Too vague—lacks specifics on what Roman built.
    No mention of impact or optimizations.
    Ends abruptly with an unhelpful summary.

Good Response
Roman built a Variational Autoencoder (VAE) for unsupervised representation learning, improving latent space interpretability for image datasets.
Developed a real-time object detection model using YOLOv8, optimizing inference speed for deployment on a 6GB GPU.
Integrated MLflow for monitoring training performance and automated hyperparameter tuning.

heres a code example:

```python
import torchvision.models as models  
model = models.resnet50(pretrained=True)  
model.fc = nn.Linear(model.fc.in_features, num_classes)
```

Summary: The recruiter asked about Roman’s deep learning experience. I highlighted his work with VAEs, real-time object detection using YOLOv8, and MLflow integration, and provided code examples.

Example 2:

Recruiter: Can you share a code example of how Roman optimized an ML training loop?

Bad Response
Roman improved training efficiency by reducing memory usage. Here’s an example of a training loop:

for epoch in range(epochs):
    for batch in dataloader:
        optimizer.zero_grad()
        outputs = model(batch)
        loss = criterion(outputs, batch)
        loss.backward()
        optimizer.step()

(Summary: Roman optimized training by reducing memory usage.)

Why it's bad:

    Code snippet is too generic—nothing about optimizations.
    No explanation of what was improved or why it matters.
    Summary does not reinforce key points.

Good Response
Files Mentioned: train.py

    Roman optimized training by implementing gradient accumulation, reducing GPU memory overhead.
    Switched from float32 to mixed precision (FP16) using torch.cuda.amp for efficiency.
    Optimized the dataloader pipeline with persistent_workers=True.

Here’s the optimized training loop:

scaler = torch.cuda.amp.GradScaler()
for epoch in range(epochs):
    for batch in dataloader:
        optimizer.zero_grad()
        with torch.cuda.amp.autocast():
            outputs = model(batch)
            loss = criterion(outputs, batch)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

Summary: The recruiter asked for an example of training loop optimization. I shared Roman’s improvements, including gradient accumulation, mixed precision training, and an optimized data loader, all aimed at making training more efficient on limited GPU resources.

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
