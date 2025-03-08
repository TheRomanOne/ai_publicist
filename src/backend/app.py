import os
import signal
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.port_manager import kill_processes_by_port
from server.config_manager import ConfigManager
from server.websocket_handler import setup_api_routes
from rag_system import RAGSystem
from chat_model_chatgpt import ChatModelChatGPT

# Clear screen and load environment variables
os.system('clear')
load_dotenv()

# Setup paths and configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
config_manager = ConfigManager(PROJECT_ROOT)
config = config_manager.get_config()

# Clean up ports
for port in [config["backend"]["port"], config["frontend"]["port"]]:
    print(f"\nChecking port {port}...")
    kill_processes_by_port(port)

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
rag_system = RAGSystem(
    code_directories=config["rag"]["code_directories"],
    embeddings_cache=config["rag"]["embeddings_cache"],
    chunk_size=config["backend"]["chunk_size"]
)

# Use ChatGPT for the chat model
chat_model = ChatModelChatGPT(
    api_key=config["backend"]["openai"]["api_key"],
    model=config["backend"]["openai"]["model"]
)

# Set up API routes
api_handler = setup_api_routes(app, rag_system, chat_model)

def cleanup_on_exit():
    """Cleanup function to run when the server is shutting down."""
    print("\nCleaning up before exit...")
    for port in [config["backend"]["port"], config["frontend"]["port"]]:
        kill_processes_by_port(port)
    exit(0)

if __name__ == "__main__":
    # Register cleanup function
    signal.signal(signal.SIGINT, cleanup_on_exit)
    signal.signal(signal.SIGTERM, cleanup_on_exit)
    
    import uvicorn
    uvicorn.run(
        app,
        host=config["backend"]["host"],
        port=config["backend"]["port"],
        timeout_keep_alive=300
    ) 