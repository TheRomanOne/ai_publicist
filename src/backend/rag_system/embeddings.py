import numpy as np
from typing import List, Union
import logging
from transformers import AutoTokenizer, AutoModel
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingModel:
    """
    Embedding model for code based on CodeBERT.
    """
    
    def __init__(self, model_name: str = "microsoft/codebert-base"):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the Hugging Face model to use
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        self.model.to(self.device)
        
        # Set model to evaluation mode
        self.model.eval()
        
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings.
        
        Returns:
            Embedding dimension
        """
        return self.model.config.hidden_size
        
    def encode(self, text: str) -> np.ndarray:
        """
        Encode a single text string.
        
        Args:
            text: Text to encode
            
        Returns:
            Embedding vector as numpy array
        """
        # Tokenize input
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=512
        ).to(self.device)
        
        # Get model output
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Use mean of last hidden state as embedding
        embeddings = outputs.last_hidden_state.mean(dim=1)
        
        return embeddings.cpu().numpy().flatten()
        
    def encode_batch(self, texts: List[str], batch_size: int = 8, progress_callback=None) -> np.ndarray:
        """
        Encode a batch of texts.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for processing
            progress_callback: Optional callback for progress reporting
            
        Returns:
            Array of embedding vectors
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch_texts, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            ).to(self.device)
            
            # Get model output
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Use mean of last hidden state as embedding
            batch_embeddings = outputs.last_hidden_state.mean(dim=1)
            all_embeddings.append(batch_embeddings.cpu().numpy())
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback(len(batch_texts))
            
        return np.vstack(all_embeddings) 