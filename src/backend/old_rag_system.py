import os
import numpy as np
import faiss
import re
import glob
from typing import List, Dict, Any
import logging
from transformers import AutoTokenizer, AutoModel
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    """Simple RAG system for code retrieval using FAISS."""
    
    def __init__(self, code_directories: List[str], embeddings_cache: str, chunk_size: int = 1500):
        """Initialize RAG system."""
        self.code_directories = code_directories
        self.embeddings_cache = embeddings_cache
        self.chunk_size = chunk_size
        self.chunks = []
        self.metadata = []
        self.index = None
        
        # Initialize embedding model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        self.model = AutoModel.from_pretrained("microsoft/codebert-base")
        self.model.to(self.device)
        self.model.eval()
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(embeddings_cache), exist_ok=True)
        
        # Load or create index
        if os.path.exists(embeddings_cache):
            self._load_from_cache()
        else:
            self._build_index()
    
    def _load_from_cache(self):
        """Load embeddings from cache file."""
        try:
            logger.info(f"Loading embeddings from cache: {self.embeddings_cache}")
            cache_data = np.load(self.embeddings_cache, allow_pickle=True)
            
            embeddings = cache_data['embeddings']
            self.chunks = cache_data['chunks'].tolist()
            self.metadata = cache_data['metadata'].tolist()
            
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings)
            
            logger.info(f"Loaded {len(self.chunks)} code chunks from cache")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self._build_index()
    
    def _build_index(self):
        """Build a new index from code files."""
        logger.info("Building new index from code directories")
        
        # Get all Python files
        all_files = []
        for directory in self.code_directories:
            if os.path.exists(directory):
                for root, _, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.py'):
                            all_files.append(os.path.join(root, file))
            else:
                logger.warning(f"Directory does not exist: {directory}")
        
        # Index files
        for file_path in all_files:
            self._index_file(file_path)
        
        # Create index
        if not self.chunks:
            logger.warning("No code chunks were indexed!")
            self.index = faiss.IndexFlatL2(768)  # Default CodeBERT dimension
            return
        
        # Generate embeddings
        embeddings = self._generate_embeddings(self.chunks)
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        
        # Save to cache
        np.savez_compressed(
            self.embeddings_cache,
            embeddings=embeddings,
            chunks=np.array(self.chunks, dtype=object),
            metadata=np.array(self.metadata, dtype=object)
        )
        
        logger.info(f"Indexed {len(self.chunks)} code chunks from {len(all_files)} files")
    
    def _index_file(self, file_path: str):
        """Index a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                return
            
            # Simple chunking by function/class or fixed size
            chunks = self._chunk_code(content, file_path)
            
            # Add chunks to index
            for chunk_text, metadata in chunks:
                self.chunks.append(chunk_text)
                self.metadata.append(metadata)
                
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
    
    def _chunk_code(self, content: str, file_path: str):
        """Chunk code into sections."""
        chunks = []
        lines = content.split('\n')
        
        # Try to identify functions and classes with regex
        func_pattern = re.compile(r'^\s*(def|class)\s+(\w+)')
        
        current_chunk = []
        current_start = 0
        in_function = False
        function_name = None
        
        for i, line in enumerate(lines):
            match = func_pattern.match(line)
            
            # New function/class found
            if match and not in_function:
                # Save previous chunk if it exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    metadata = {
                        'file_path': os.path.relpath(file_path),
                        'start_line': current_start + 1,
                        'end_line': i,
                        'function_name': None
                    }
                    chunks.append((chunk_text, metadata))
                
                # Start new function/class chunk
                current_chunk = [line]
                current_start = i
                in_function = True
                function_name = match.group(2)
                
            # End of function/class (indentation decreased)
            elif in_function and line.strip() and len(line) - len(line.lstrip()) <= len(lines[current_start]) - len(lines[current_start].lstrip()):
                # Save the function chunk
                chunk_text = '\n'.join(current_chunk)
                metadata = {
                    'file_path': os.path.relpath(file_path),
                    'start_line': current_start + 1,
                    'end_line': i,
                    'function_name': function_name
                }
                chunks.append((chunk_text, metadata))
                
                # Start new chunk
                current_chunk = [line]
                current_start = i
                in_function = False
                function_name = None
                
            # Continue current chunk
            else:
                current_chunk.append(line)
        
        # Add the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            metadata = {
                'file_path': os.path.relpath(file_path),
                'start_line': current_start + 1,
                'end_line': len(lines),
                'function_name': function_name
            }
            chunks.append((chunk_text, metadata))
        
        # If the file is too large, also create fixed-size chunks
        if len(content) > self.chunk_size:
            # Create overlapping fixed-size chunks
            for i in range(0, len(content), self.chunk_size // 2):
                chunk_text = content[i:i+self.chunk_size]
                if len(chunk_text) < 100:  # Skip very small chunks
                    continue
                    
                # Estimate line numbers
                start_line = content[:i].count('\n') + 1
                end_line = start_line + chunk_text.count('\n')
                
                metadata = {
                    'file_path': os.path.relpath(file_path),
                    'start_line': start_line,
                    'end_line': end_line,
                    'function_name': None
                }
                chunks.append((chunk_text, metadata))
        
        return chunks
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of text chunks."""
        all_embeddings = []
        batch_size = 8
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            # Tokenize
            inputs = self.tokenizer(
                batch_texts, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Use mean of last hidden state
            batch_embeddings = outputs.last_hidden_state.mean(dim=1)
            all_embeddings.append(batch_embeddings.cpu().numpy())
            
        return np.vstack(all_embeddings)
    
    def get_relevant_context(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant code chunks for a query."""
        if not self.index or self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        inputs = self.tokenizer(
            query, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=512
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        query_embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        
        # Search for similar chunks
        top_k = min(top_k, self.index.ntotal)
        _, indices = self.index.search(query_embedding, top_k)
        
        # Format results
        results = []
        for idx in indices[0]:
            if idx >= 0 and idx < len(self.chunks):
                chunk = self.chunks[idx]
                metadata = self.metadata[idx]
                
                formatted_chunk = f"File: {metadata['file_path']}\n"
                if metadata['function_name']:
                    formatted_chunk += f"Function: {metadata['function_name']}\n"
                formatted_chunk += f"Lines {metadata['start_line']}-{metadata['end_line']}\n\n"
                formatted_chunk += chunk
                
                results.append(formatted_chunk)
        
        return results
    
    def refresh_index(self):
        """Rebuild the index from scratch."""
        self._build_index()
        return {"status": "success", "chunks_indexed": len(self.chunks)} 