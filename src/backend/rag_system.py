import os
from typing import List
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm
import ast

class RAGSystem:
    """Retrieval-Augmented Generation system for code context."""
    
    def __init__(self, code_directories: List[str], embeddings_cache: str, chunk_size: int = 1500):
        """Initialize the RAG system."""
        self.code_directories = code_directories
        self.embeddings_cache = embeddings_cache
        self.chunk_size = chunk_size
        
        print(f"Initializing RAG system with directories: {code_directories}")
        
        self.model_name = 'microsoft/codebert-base'
        
        # Load or create embeddings
        if os.path.exists(embeddings_cache):
            print(f"Loading existing embeddings from {embeddings_cache}")
            cached_data = np.load(embeddings_cache)
            self.embeddings = cached_data['embeddings']
            self.chunks = cached_data['chunks'].tolist()
        else:
            print("Creating new embeddings...")
            self.chunks = self._process_directories()
            self.embeddings = self._create_embeddings()
            
            # Save embeddings
            os.makedirs(os.path.dirname(embeddings_cache), exist_ok=True)
            np.savez(
                embeddings_cache,
                embeddings=self.embeddings,
                chunks=np.array(self.chunks)
            )
        
        print(f"Loaded {len(self.chunks)} chunks")

    def _process_file(self, file_path):
        """Process a single file and break it into chunks.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List of text chunks from the file
        """
        # Skip non-text files or files that are too large
        if not self._is_text_file(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip empty or very small files
            if len(content) < 50:
                return []
            
            # Add file path as metadata
            content = f"FILE: {file_path}\n\n{content}"
            
            # Break content into chunks
            chunks = []
            current_chunk = ""
            
            for line in content.split('\n'):
                if len(current_chunk) + len(line) + 1 <= self.chunk_size:
                    current_chunk += line + '\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = line + '\n'
            
            # Add the last chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks
        
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return []

    def _process_directories(self) -> List[str]:
        """Process all files in the given directories."""
        chunks = []
        for directory in self.code_directories:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py'):  # Only process Python files
                        file_path = os.path.join(root, file)
                        print(f"Processing file: {file_path}")  # Debug log
                        chunks.extend(self._process_file(file_path))
        return chunks

    def _create_embeddings(self) -> np.ndarray:
        """Create embeddings for all chunks."""
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModel.from_pretrained(self.model_name)
        device = "cpu"  # Force CPU
        model = model.to(device)
        model.eval()
        
        # Create embeddings
        embeddings = []
        for chunk in tqdm(self.chunks, desc="Creating embeddings"):
            inputs = tokenizer(chunk, return_tensors='pt', truncation=True, max_length=512).to(device)
            with torch.no_grad():
                outputs = model(**inputs)
            embeddings.append(outputs.last_hidden_state.mean(dim=1).cpu().numpy())
        
        return np.vstack(embeddings)

    def get_relevant_context(self, query: str, top_k: int = 3) -> List[str]:
        """Get the most relevant chunks for a query."""
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModel.from_pretrained(self.model_name)
        device = "cpu"  # Force CPU
        model = model.to(device)
        model.eval()
                
        inputs = tokenizer(query, return_tensors='pt', truncation=True, max_length=512).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        query_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        
        # Calculate similarities
        similarities = np.dot(self.embeddings, query_embedding.T).squeeze()
        top_indices = np.argsort(similarities)[-top_k:][::-1]
                
        return [self.chunks[i] for i in top_indices]

    def _is_text_file(self, file_path: str) -> bool:
        """Check if a file is a Python file that can be processed.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file is a valid Python file, False otherwise
        """
        # Check if it's a Python file
        if not file_path.endswith('.py'):
            return False
        
        # Check file size (skip files larger than 1MB)
        try:
            if os.path.getsize(file_path) > 1024 * 1024:
                print(f"Skipping large file: {file_path}")
                return False
            
            # Just check if it's readable
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(10)  # Just test if readable
            return True
        
        except Exception as e:
            print(f"Skipping inaccessible file: {file_path} ({str(e)})")
            return False