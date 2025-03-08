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

    def _process_file(self, file_path: str) -> List[str]:
        """Process a single file into structural chunks (functions/classes)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = []
        try:
            # Parse Python file
            tree = ast.parse(content)
            
            # Get imports section
            imports = []
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_lines = content.splitlines()[node.lineno-1:node.end_lineno]
                    imports.extend(import_lines)
            
            imports_text = "\n".join(imports)
            
            # Process each function and class
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    # Get the source lines for this definition
                    func_lines = content.splitlines()[node.lineno-1:node.end_lineno]
                    func_text = "\n".join(func_lines)
                    
                    # Include imports with each function for context
                    chunk_text = f"File: {file_path}\n\n# Imports\n{imports_text}\n\n# Definition\n{func_text}"
                    chunks.append(chunk_text)
            
            # If no functions/classes found, use the current chunking method
            if not chunks:
                return self._process_file(file_path)
            
            return chunks
        
        except SyntaxError:
            # Fall back to the original method if the file has syntax errors
            return self._process_file(file_path)

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