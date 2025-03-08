import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, project_root: str):
        self.project_root = project_root
        load_dotenv(os.path.join(project_root, '.env'))  # Load environment variables
        self.config = self._load_config()
        self._process_paths()
        self._process_env_vars()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json."""
        config_path = os.path.join(self.project_root, "config.json")
        with open(config_path) as f:
            return json.load(f)
    
    def _process_paths(self) -> None:
        """Convert relative paths to absolute paths."""
        for i, dir_path in enumerate(self.config["rag"]["code_directories"]):
            self.config["rag"]["code_directories"][i] = os.path.join(
                self.project_root, 
                dir_path.lstrip("./")
            )
        
        self.config["rag"]["embeddings_cache"] = os.path.join(
            self.project_root, 
            self.config["rag"]["embeddings_cache"].lstrip("./")
        )
        
    
    def _process_env_vars(self) -> None:
        """Process environment variables."""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.config["backend"]["openai"]["api_key"] = openai_api_key
        else:
            print("Warning: OPENAI_API_KEY not found in environment variables")
    
    def get_config(self) -> Dict[str, Any]:
        """Get the processed configuration."""
        return self.config 