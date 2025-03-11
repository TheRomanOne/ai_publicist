import os
import signal
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.port_manager import kill_processes_by_port
from server.config_manager import ConfigManager
from server.websocket_handler import setup_api_routes
from rag_system.rag_system import RAGSystem
from chat_model_chatgpt import ChatModelChatGPT

# Clear screen and load environment variables
os.system('clear')
load_dotenv()

# Setup paths and configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
config_manager = ConfigManager(PROJECT_ROOT)
config = config_manager.get_config()

# Initialize FastAPI app
app = FastAPI(title="RAG Chat API", 
              description="REST API for chat with retrieval-augmented generation")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For a production app, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize systems
chunking_config = config["backend"].get("chunking", {})
rag_system = RAGSystem(
    code_directories=config["rag"]["code_directories"],
    embeddings_cache=config["rag"]["embeddings_cache"],
    chunk_size=config["backend"]["chunk_size"],  
    min_lines=chunking_config.get("min_lines"),
    preferred_lines=chunking_config.get("preferred_lines"),
    overlap_percentage=chunking_config.get("overlap_percentage")
)

# Use ChatGPT for the chat model
chat_model = ChatModelChatGPT(
    api_key=config["backend"]["openai"]["api_key"],
    model=config["backend"]["openai"]["model"],
    user_name=config["user_name"]
)

# Extract max_context_chunks from config
retrieved_chunks = config["backend"]["max_context_chunks"]

# Set up API routes
resume_path = os.path.join(PROJECT_ROOT, "src/backend/resume.txt")
api_handler = setup_api_routes(app, rag_system, chat_model, retrieved_chunks, resume_path)

def cleanup():
    """Cleanup function to run when the server is shutting down."""
    print("\nCleaning up ports")
    for port in [config["backend"]["port"]]:#, config["frontend"]["port"]]:
        kill_processes_by_port(port)

if __name__ == "__main__":
    # Register cleanup function
    cleanup()
    
    import uvicorn
    uvicorn.run(
        app,
        host=config["backend"]["host"],
        port=config["backend"]["port"],
        timeout_keep_alive=300
    ) 