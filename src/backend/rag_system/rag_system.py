import os
import faiss
import numpy as np
import time
from typing import List, Dict, Any, Tuple
import logging
from .code_indexer import CodeIndexer
from .embeddings import EmbeddingModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGSystem:
    """
    Retrieval-Augmented Generation system for code retrieval.
    Uses FAISS for efficient similarity search on code embeddings.
    """
    
    def __init__(self, code_directories: List[str], embeddings_cache: str, 
                 chunk_size: int = 1500, min_lines: int = 50, 
                 preferred_lines: int = 100, overlap_percentage: int = 5,
                 progress_handler=None):
        """
        Initialize RAG system.
        
        Args:
            code_directories: List of directories containing Python code
            embeddings_cache: Path to cache file for embeddings
            chunk_size: Size of code chunks for indexing
            min_lines: Minimum lines for any chunk to be included
            preferred_lines: Preferred minimum lines before considering splitting a chunk
            overlap_percentage: Percentage of overlap between chunks (1-100)
            progress_handler: Optional handler for progress reporting
        """
        self.code_directories = code_directories
        self.embeddings_cache = embeddings_cache
        self.chunk_size = chunk_size
        self.progress_handler = progress_handler
        self.embedding_model = EmbeddingModel()
        self.code_indexer = CodeIndexer(
            chunk_size=chunk_size,
            min_lines=min_lines,
            preferred_lines=preferred_lines,
            overlap_percentage=overlap_percentage,
        )
        
        self.index = None
        self.code_chunks = []
        self.code_metadata = []
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(embeddings_cache), exist_ok=True)
        
        # Load or create index
        self._load_or_create_index()
        
    def _load_or_create_index(self):
        """Load existing index from cache or create a new one."""
        if os.path.exists(self.embeddings_cache):
            try:
                logger.info(f"Loading embeddings from cache: {self.embeddings_cache}")
                cache_data = np.load(self.embeddings_cache, allow_pickle=True)
                
                # Load embeddings and metadata
                embeddings = cache_data['embeddings']
                self.code_chunks = cache_data['chunks'].tolist()
                self.code_metadata = cache_data['metadata'].tolist()
                
                # Create and populate FAISS index
                self.index = faiss.IndexFlatL2(embeddings.shape[1])
                self.index.add(embeddings)
                
                logger.info(f"Loaded {len(self.code_chunks)} code chunks from cache")
                return
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                logger.info("Building new index...")
        
        # Build new index if cache doesn't exist or is invalid
        self._build_index()
        
    def _build_index(self):
        """Build a new FAISS index from code directories."""
        start_time = time.time()
        logger.info(f"Building index from code directories: {self.code_directories}")
        
        # Index code files
        for directory in self.code_directories:
            self.code_indexer.index_directory(directory)
        
        # Get chunks and metadata
        chunks, metadata = self.code_indexer.get_indexed_chunks()
        self.code_chunks = chunks
        self.code_metadata = metadata
        
        if not chunks:
            logger.warning("No code chunks were indexed!")
            # Create empty index
            self.index = faiss.IndexFlatL2(self.embedding_model.get_embedding_dimension())
            return
        
        # Generate embeddings for all chunks with progress reporting
        logger.info(f"Generating embeddings for {len(chunks)} code chunks...")
        
        # Set up progress handler if provided
        if self.progress_handler:
            with self.progress_handler as progress:
                progress.set_total(len(chunks))
                embeddings = self.embedding_model.encode_batch(chunks, progress_callback=progress.update)
        else:
            embeddings = self.embedding_model.encode_batch(chunks)
        
        # Create and populate FAISS index
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        
        # Save to cache
        self._save_to_cache(embeddings)
        
        logger.info(f"Indexed {len(chunks)} code chunks in {time.time() - start_time:.2f} seconds")
        
    def _save_to_cache(self, embeddings):
        """Save index data to cache file."""
        logger.info(f"Saving embeddings to cache: {self.embeddings_cache}")
        np.savez_compressed(
            self.embeddings_cache,
            embeddings=embeddings,
            chunks=np.array(self.code_chunks, dtype=object),
            metadata=np.array(self.code_metadata, dtype=object)
        )
        
    def get_relevant_context(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve relevant code chunks for a given query.
        
        Args:
            query: The query text
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant code chunks as strings
        """
        if not self.index or self.index.ntotal == 0:
            logger.warning("Index is empty, no context available")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Reshape for FAISS
        query_embedding = query_embedding.reshape(1, -1)
        
        # Search the index
        top_k = min(top_k, self.index.ntotal)  # Make sure we don't ask for more than we have
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Retrieve the corresponding chunks
        results = []
        for idx in indices[0]:
            if idx >= 0 and idx < len(self.code_chunks):  # Ensure valid index
                chunk = self.code_chunks[idx]
                metadata = self.code_metadata[idx]
                
                # Format the chunk with its metadata
                formatted_chunk = f"File: {metadata['file_path']}\n"
                if 'function_name' in metadata and metadata['function_name']:
                    formatted_chunk += f"Function: {metadata['function_name']}\n"
                formatted_chunk += f"Lines {metadata['start_line']}-{metadata['end_line']}\n\n"
                formatted_chunk += chunk
                
                results.append(formatted_chunk)
        
        return results
    
    def refresh_index(self):
        """Rebuild the index from scratch."""
        logger.info("Refreshing code index...")
        self._build_index()
        return {"status": "success", "chunks_indexed": len(self.code_chunks)} 