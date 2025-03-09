import os
import sys
import json
import argparse
import logging
import time
import random
from tqdm import tqdm
from rag_system.rag_system import RAGSystem
from server.config_manager import ConfigManager
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

# Setup prettier logging with minimal timestamp
logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def log_info(msg):
    """Print a nicely formatted info message"""
    logger.info(f"{Fore.GREEN}→{Style.RESET_ALL} {msg}")

def log_warn(msg):
    """Print a nicely formatted warning message"""
    logger.warning(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {msg}")

def log_success(msg):
    """Print a nicely formatted success message"""
    logger.info(f"{Fore.GREEN}✓{Style.RESET_ALL} {msg}")

def log_step(step, msg):
    """Print a nicely formatted step message"""
    logger.info(f"{Fore.BLUE}[{step}]{Style.RESET_ALL} {msg}")

def init_rag_system(config_path=None, verbose=True):
    """Initialize the RAG system with friendly logging and progress information."""
    start_time = time.time()
    
    # Print welcome message
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'🤖 RAG System Initializer 🤖':^70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    # Step 1: Find project and configuration
    log_step("1/4", "Finding project and configuration files")
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_info(f"Project located at: {project_root}")
    
    # Load configuration
    if config_path:
        log_info(f"Using custom config from: {os.path.basename(config_path)}")
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        log_info(f"Using default config from config.json")
        config_manager = ConfigManager(project_root)
        config = config_manager.get_config()
   
    # Step 2: Verify code directories
    log_step("2/4", "Checking source code directories")
    
    # The directory paths in config file are already absolute
    code_directories = config['rag']['code_directories']
    valid_dirs = 0
    
    for i, directory in enumerate(code_directories):
        if os.path.exists(directory):
            log_info(f"Found code directory: {os.path.basename(directory)}")
            valid_dirs += 1
        else:
            log_warn(f"Directory not found: {directory}")
    
    if valid_dirs == 0:
        log_warn("No valid code directories found. Check your config.json file.")
    else:
        log_success(f"Found {valid_dirs} valid code {_plural('directory', valid_dirs)}")
    
    # Step 3: Set up cache
    log_step("3/4", "Setting up embeddings cache")
    
    # Make sure cache path is absolute
    embeddings_cache = config['rag']['embeddings_cache']
    if not os.path.isabs(embeddings_cache):
        embeddings_cache = os.path.join(project_root, embeddings_cache)
    
    # Always remove existing cache to ensure freshness
    if os.path.exists(embeddings_cache):
        log_info(f"Removing existing cache file")
        os.remove(embeddings_cache)
    
    cache_dir = os.path.dirname(embeddings_cache)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        log_info(f"Created cache directory: {cache_dir}")
    
    # Step 4: Initialize RAG system
    log_step("4/4", "Building code index and generating embeddings")
    
    # Create a custom tqdm instance for progress reporting
    class TqdmLoggingHandler:
        def __init__(self, desc):
            self.pbar = None
            self.desc = desc
            
        def __enter__(self):
            return self
            
        def update(self, n=1):
            if self.pbar:
                self.pbar.update(n)
            
        def set_total(self, total):
            if verbose and total > 0:
                self.pbar = tqdm(
                    total=total, 
                    desc=self.desc,
                    bar_format='{l_bar}{bar:30}{r_bar}',
                    colour='green'
                )
                
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.pbar:
                self.pbar.close()
    
    # Initialize RAG system
    rag_system = RAGSystem(
        code_directories=code_directories,
        embeddings_cache=embeddings_cache,
        chunk_size=config['backend']['chunk_size'],
        progress_handler=TqdmLoggingHandler("Processing code")
    )
    
    # Log statistics
    total_time = time.time() - start_time
    chunks_count = len(rag_system.code_chunks)
    
    # Print summary
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'📊 Summary 📊':^70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
    
    log_success(f"Indexed {chunks_count} code {_plural('chunk', chunks_count)} from {valid_dirs} {_plural('directory', valid_dirs)}")
    log_success(f"Process completed in {total_time:.1f} seconds")
    log_success(f"Cache saved to: {os.path.basename(embeddings_cache)}")
    
    # Display a random chunk if any were indexed
    if chunks_count > 0:
        random_idx = random.randint(0, chunks_count - 1)
        sample_chunk = rag_system.code_chunks[random_idx]
        metadata = rag_system.code_metadata[random_idx]
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'📝 Sample Code Chunk 📝':^70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}File:{Style.RESET_ALL} {metadata['file_path']}")
        if 'function_name' in metadata and metadata['function_name']:
            print(f"{Fore.YELLOW}Function:{Style.RESET_ALL} {metadata['function_name']}")
        print(f"{Fore.YELLOW}Lines:{Style.RESET_ALL} {metadata['start_line']}-{metadata['end_line']}")
        print(f"\n{Fore.GREEN}```python{Style.RESET_ALL}")
        # Show at most 15 lines from the chunk
        chunk_lines = sample_chunk.split('\n')
        display_lines = chunk_lines[:15]
        print('\n'.join(display_lines))
        if len(chunk_lines) > 15:
            print(f"{Fore.YELLOW}... ({len(chunk_lines) - 15} more lines){Style.RESET_ALL}")
        print(f"{Fore.GREEN}```{Style.RESET_ALL}\n")
    
    return {
        "status": "success",
        "chunks_indexed": chunks_count,
        "directories_indexed": valid_dirs,
        "time_taken": f"{total_time:.1f} seconds"
    }

def _plural(word, count):
    """Return plural form if count is not 1"""
    return word if count == 1 else word + 's'

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the RAG system")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress bars")
    args = parser.parse_args()
    
    try:
        result = init_rag_system(args.config, verbose=not args.quiet)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Process interrupted by user.{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error initializing RAG system: {e}{Style.RESET_ALL}")
        if "--verbose" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1) 