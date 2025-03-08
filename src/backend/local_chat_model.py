import torch
from typing import List
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig

class ChatModel:
    """Wrapper for the language model."""
    
    def __init__(self, model_path: str, max_context_chunks: int):
        """Initialize the chat model."""
        self.max_context_chunks = max_context_chunks
        
        # Force CPU usage
        torch.cuda.is_available = lambda: False
        self.device = torch.device("cpu")
        print(f"Using device: {self.device}")
        
        self.model_id = "microsoft/phi-2"  # Switch back to Phi-2
        
        # Check if model exists locally
        if os.path.exists(model_path):
            try:
                print(f"Attempting to load existing model from {model_path}")
                config = AutoConfig.from_pretrained(model_path)
                if hasattr(config, 'quantization_config'):
                    delattr(config, 'quantization_config')
                
                # Use simpler loading settings that worked before
                model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    config=config,
                    torch_dtype=torch.float32,
                    device_map=None,  # Changed from "auto" to None
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
                model.to('cpu')  # Explicitly move to CPU
                tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            except Exception as e:
                print(f"Error loading local model, will delete and re-download: {e}")
                import shutil
                shutil.rmtree(model_path, ignore_errors=True)
                os.makedirs(model_path, exist_ok=True)
        
        # Download model if it doesn't exist or was deleted
        if not os.path.exists(os.path.join(model_path, "pytorch_model.bin")):
            print(f"Downloading model {self.model_id}...")
            try:
                # Use simpler download settings
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float32,
                    device_map=None,  # Changed from "auto" to None
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
                model.to('cpu')  # Explicitly move to CPU
                tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
                
                print(f"Saving model to {model_path}")
                # Save model without quantization config
                config = model.config
                if hasattr(config, 'quantization_config'):
                    delattr(config, 'quantization_config')
                
                model.save_pretrained(model_path, config=config)
                tokenizer.save_pretrained(model_path)
            except Exception as e:
                print(f"Error downloading model: {e}")
                raise
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        
        self.model = model
        self.tokenizer = tokenizer
        
        # Set model to evaluation mode
        self.model.eval()
        
        # Calculate max length considering model's context window
        model_max_length = self.tokenizer.model_max_length
        print(f"Model max length: {model_max_length}")
        
        # Set generation parameters for optimal performance
        self.generation_config = {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True,
            "use_cache": True,
            "pad_token_id": tokenizer.eos_token_id,
            "repetition_penalty": 1.1
        }
        
        print("Model initialization complete!")
    
    def generate_response(self, message: str, context: List[str]) -> str:
        """Generate a response using the chat model."""
        try:
            # Create direct prompt
            prompt = f"""Based on the code below, answer the question precisely and factually.

Code context:
{chr(10).join(context)}

Question: {message}

Response:"""

            # Tokenize input
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt",
                truncation=True,
                max_length=1024
            )
            
            # Ensure all tensors are on CPU
            input_ids = inputs.input_ids.cpu()
            attention_mask = inputs.attention_mask.cpu()
            
            # Very conservative generation settings
            generation_settings = {
                "max_new_tokens": 100,      # Keep it brief
                "temperature": 0.1,         # Almost deterministic
                "top_p": 0.5,              # Very focused sampling
                "do_sample": True,
                "use_cache": True,
                "pad_token_id": self.tokenizer.eos_token_id,
                "repetition_penalty": 1.3   # Strongly avoid repetition
            }
            
            with torch.inference_mode():
                outputs = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    **generation_settings
                )
            
            # Extract response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up response - get everything after "Response:"
            try:
                response = response.split("Response:")[-1].strip()
            except:
                response = response[len(prompt):].strip()
            
            return response

        except Exception as e:
            print(f"Error processing response: {e}")
            return "I encountered an error while generating the response. Please try again." 