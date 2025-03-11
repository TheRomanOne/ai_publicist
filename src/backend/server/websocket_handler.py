import time
import sys
import traceback
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4

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

class UserNameRequest(BaseModel):
    user_name: str

class ApiHandler:
    def __init__(self, rag_system: Any, chat_model: Any, retrieved_chunks: int, resume_path: str):
        """Initialize the API handler with RAG system and chat model"""
        self.rag_system = rag_system
        self.chat_model = chat_model
        self.retrieved_chunks = retrieved_chunks
        
        # Read resume from text file
        with open(resume_path, 'r') as file:
            self.resume = file.read()
        
        # Track active sessions and their pending tasks
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.pending_tasks: Dict[str, asyncio.Task] = {}
    
    async def handle_chat_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return a response"""
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid4())
        log_message(f"Received request with session_id: {session_id}")
        
        # Initialize session data if it doesn't exist
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "last_active": datetime.now(),
                "message_count": 0,
                "chat_history": ""  # Initialize empty chat history
            }
        
        # Update session data
        self.sessions[session_id]["last_active"] = datetime.now()
        self.sessions[session_id]["message_count"] += 1
        
        start_time = time.time()
        
        try:
            # Get relevant context from RAG system
            context = self.rag_system.get_relevant_context(request.message, top_k=self.retrieved_chunks)
            log_message(f"Retrieved {len(context)} context chunks for query")
            
            # Get chat history from session
            chat_history = self.sessions[session_id].get("chat_history", "")
            
            # Generate response
            response_data = self.chat_model.generate_response(
                request.message,
                context,
                self.resume,
                chat_history
            )
            
            # Extract content and summary
            content = response_data["content"]
            summary = response_data["summary"]
            
            # Update chat history with the new summary if it exists
            if summary:
                if chat_history:
                    chat_history += "\n\n"
                chat_history += f"Q: {request.message}\nA: {summary}"
                self.sessions[session_id]["chat_history"] = chat_history
            
            request_time = time.time() - start_time
            log_message(f"Request processed in {request_time:.2f} seconds")
            
            return ChatResponse(
                content=content,
                session_id=session_id,
                request_time=request_time
            )
        
        except Exception as e:
            log_error(f"Error processing request: {str(e)}", exc_info=e)
            request_time = time.time() - start_time
            
            return ChatResponse(
                content=ERROR_MESSAGES["general"],
                session_id=session_id,
                request_time=request_time
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
def setup_api_routes(app: FastAPI, rag_system: Any, chat_model: Any, retrieved_chunks: int, resume_path: str):
    """Set up API routes for the chat application"""
    api_handler = ApiHandler(rag_system, chat_model, retrieved_chunks, resume_path)
    
    @app.post("/api/chat", response_model=ChatResponse)
    async def chat_endpoint(request: ChatRequest):
        return await api_handler.handle_chat_request(request)
    
    @app.post("/api/chat/user_name")
    async def user_name_endpoint(request: UserNameRequest):
        return await api_handler.handle_user_name_request(request)
    
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