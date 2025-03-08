import time
import sys
import traceback
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4
from resume import resume

# Error messages
ERROR_MESSAGES = {
    "general": "I encountered an error while generating the response. Please try again.",
    "timeout": "The request took too long to process. Please try a simpler query.",
    "disconnected": "The connection to the server was lost. Please try again when reconnected."
}

# Logging helpers
def log_message(message):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")

def log_error(message, exc_info=None):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] ERROR: {message}", file=sys.stderr)
    if exc_info:
        print("-" * 40, file=sys.stderr)
        traceback.print_exception(*exc_info if isinstance(exc_info, tuple) else (type(exc_info), exc_info, exc_info.__traceback__))
        print("-" * 40, file=sys.stderr)

# Request and response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    content: str
    session_id: str
    request_time: float

class ApiHandler:
    def __init__(self, rag_system: Any, chat_model: Any):
        """Initialize the API handler with RAG system and chat model"""
        self.rag_system = rag_system
        self.chat_model = chat_model
        # Track active sessions and their pending tasks
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.pending_tasks: Dict[str, asyncio.Task] = {}
        self.resume = resume
    async def handle_chat_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return a response"""
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid4())
        log_message(f"Received request with session_id: {session_id}")
        
        try:
            # Store session timestamp
            self.sessions[session_id] = {
                "last_active": datetime.now(),
                "message_count": self.sessions.get(session_id, {}).get("message_count", 0) + 1
            }
            
            # Get the user message
            message = request.message
            log_message(f"Processing message for session {session_id}: {message[:30]}{'...' if len(message) > 30 else ''}")
            
            # Get relevant context from RAG system
            start_time = time.time()
            context = []
            try:
                context = self.rag_system.get_relevant_context(message, top_k=3)
                log_message(f"Retrieved {len(context)} context chunks for query")
            except Exception as e:
                log_error(f"Error getting context: {e}", exc_info=e)
            
            # Generate response using the chat model
            try:
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: self.chat_model.generate_response(message, context, self.resume)
                    ),
                    timeout=120
                )
            except asyncio.TimeoutError:
                log_error(f"Response generation timed out for session {session_id}")
                return ChatResponse(
                    content=ERROR_MESSAGES["timeout"],
                    session_id=session_id,
                    request_time=time.time() - start_time
                )
            except Exception as e:
                log_error(f"Error generating response: {e}", exc_info=e)
                return ChatResponse(
                    content=ERROR_MESSAGES["general"],
                    session_id=session_id,
                    request_time=time.time() - start_time
                )
            
            # Process the response
            content = response.strip()
            if response.startswith("Error:"):
                log_error(f"Model returned error: {content[:100]}")
                content = ERROR_MESSAGES["general"]
            
            
            # Return formatted response
            elapsed = time.time() - start_time
            log_message(f"Response generated in {elapsed:.2f}s for session {session_id}")
            
            return ChatResponse(
                content=content,
                session_id=session_id,
                request_time=elapsed
            )
            
        except Exception as e:
            log_error(f"Unexpected error in request handler: {e}", exc_info=e)
            return ChatResponse(
                content=ERROR_MESSAGES["general"],
                session_id=session_id,
                request_time=0.0
            )
    
    async def cleanup_sessions(self):
        """Cleanup inactive sessions (run periodically)"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            # Check if session has been inactive for more than 30 minutes
            if (now - session_data["last_active"]).total_seconds() > 1800:
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            if session_id in self.sessions:
                del self.sessions[session_id]
                log_message(f"Cleaned up inactive session {session_id}")

# Create a function to add API routes to a FastAPI app
def setup_api_routes(app: FastAPI, rag_system: Any, chat_model: Any):
    """Set up API routes for the chat application"""
    api_handler = ApiHandler(rag_system, chat_model)
    
    @app.post("/api/chat", response_model=ChatResponse)
    async def chat_endpoint(request: ChatRequest):
        return await api_handler.handle_chat_request(request)
    
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "ok", "active_sessions": len(api_handler.sessions)}
    
    # Set up background task for session cleanup
    @app.on_event("startup")
    async def startup_event():
        asyncio.create_task(periodic_cleanup(api_handler))
    
    return api_handler

async def periodic_cleanup(api_handler: ApiHandler):
    """Run periodic cleanup of inactive sessions"""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        try:
            await api_handler.cleanup_sessions()
        except Exception as e:
            log_error(f"Error in session cleanup: {e}") 