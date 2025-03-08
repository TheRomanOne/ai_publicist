import os
import json
from rag_system import RAGSystem

# Get the directory containing this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (one level up from backend)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

def init_rag():
    # Load configuration
    config_path = os.path.join(PROJECT_ROOT, "config.json")
    with open(config_path) as f:
        config = json.load(f)

    # Convert relative paths to absolute paths
    code_directories = []
    for dir_path in config["rag"]["code_directories"]:
        # Keep absolute paths as is, convert relative paths
        if os.path.isabs(dir_path):
            code_directories.append(dir_path)
        else:
            code_directories.append(os.path.join(PROJECT_ROOT, dir_path.lstrip("./")))

    embeddings_cache = os.path.join(PROJECT_ROOT, config["rag"]["embeddings_cache"].lstrip("./"))

    # Delete existing cache if it exists
    if os.path.exists(embeddings_cache):
        print(f"Deleting existing embeddings cache: {embeddings_cache}")
        os.remove(embeddings_cache)

    # Initialize RAG system
    print("Initializing RAG system...")
    print(f"Directories to index: {code_directories}")
    
    RAGSystem(
        code_directories=code_directories,
        embeddings_cache=embeddings_cache,
        chunk_size=config["backend"]["chunk_size"]
    )

if __name__ == "__main__":
    os.system('clear')  # Only clear screen when run as script
    init_rag() 