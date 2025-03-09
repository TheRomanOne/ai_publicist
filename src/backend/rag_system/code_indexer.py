import os
import re
import ast
import logging
from typing import List, Dict, Tuple, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeIndexer:
    """
    Indexer for Python code files.
    Processes Python files and breaks them into chunks with appropriate metadata.
    """
    
    def __init__(self, chunk_size: int = 1500, min_lines: int = 50, 
                 preferred_lines: int = 100, overlap_percentage: int = 5):
        """
        Initialize code indexer.
        
        Args:
            chunk_size: Maximum size of code chunks in characters (legacy parameter, not used)
            min_lines: Minimum lines for any chunk to be included
            preferred_lines: Preferred minimum lines before considering splitting a chunk
            overlap_percentage: Percentage of overlap between chunks (1-100)
        """
        self.chunk_size = chunk_size
        self.min_lines = min_lines
        self.preferred_lines = preferred_lines
        self.overlap_percentage = overlap_percentage
        self.chunks = []
        self.metadata = []
        
    def index_directory(self, directory_path: str) -> None:
        """
        Index all Python files in a directory and its subdirectories.
        
        Args:
            directory_path: Path to the directory
        """
        if not os.path.exists(directory_path):
            logger.warning(f"Directory does not exist: {directory_path}")
            return
            
        logger.info(f"Indexing directory: {directory_path}")
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self._index_file(file_path)
    
    def _index_file(self, file_path: str) -> None:
        """
        Index a single Python file.
        
        Args:
            file_path: Path to the Python file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Skip if file is empty
            if not content.strip():
                return
                
            # Process the file content
            self._process_file_content(content, file_path)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def _process_file_content(self, content: str, file_path: str) -> None:
        """
        Process content of a Python file.
        
        Args:
            content: File content
            file_path: Path to the file
        """
        # Try to parse the file with AST to extract functions and classes
        try:
            tree = ast.parse(content)
            
            # Process function and class definitions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    node_name = node.name
                    node_type = 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
                    
                    # Get node's code lines
                    start_line = node.lineno
                    end_line = self._find_node_end_line(content, node)
                    
                    # Get node's code
                    lines = content.split('\n')
                    node_code = '\n'.join(lines[start_line-1:end_line])
                    
                    # Create chunks from the node's code
                    self._create_chunks(node_code, file_path, node_type, node_name, start_line, end_line)
            
            # Also chunk the entire file for context
            self._create_chunks(content, file_path, 'file', os.path.basename(file_path), 1, len(content.split('\n')))
            
        except SyntaxError:
            # If AST parsing fails, just chunk the file as plain text
            self._create_chunks(content, file_path, 'file', os.path.basename(file_path), 1, len(content.split('\n')))
    
    def _find_node_end_line(self, content: str, node: ast.AST) -> int:
        """
        Find the last line of a node.
        
        Args:
            content: File content
            node: AST node
            
        Returns:
            End line number
        """
        lines = content.split('\n')
        
        # Start from the node's first line
        line_number = node.lineno
        indentation = len(lines[line_number-1]) - len(lines[line_number-1].lstrip())
        
        # Find the end by looking for the next line with same or less indentation
        while line_number < len(lines):
            # Skip empty lines
            if not lines[line_number].strip():
                line_number += 1
                continue
                
            # If we find a line with same or less indentation, we've reached the end
            current_indent = len(lines[line_number]) - len(lines[line_number].lstrip())
            if current_indent <= indentation and line_number > node.lineno:
                break
                
            line_number += 1
            
        return min(line_number, len(lines))
    
    def _create_chunks(self, code: str, file_path: str, node_type: str, node_name: str, 
                       start_line: int, end_line: int) -> None:
        """
        Create chunks from code.
        
        Args:
            code: Source code to chunk
            file_path: Path to the source file
            node_type: Type of node ('function', 'class', 'module')
            node_name: Name of the node
            start_line: Starting line number
            end_line: Ending line number
        """
        # Skip empty code
        if not code.strip():
            return
        
        # Get relative path for display
        try:
            relative_path = os.path.relpath(file_path)
        except:
            relative_path = file_path
        
        # Split into lines
        lines = code.split('\n')
        
        # Initialize chunking variables
        current_chunk = []
        current_size = 0
        chunk_start_line = start_line
        
        # Process line by line
        for i, line in enumerate(lines):
            # Add line to current chunk
            current_chunk.append(line)
            
            # Check if current chunk is large enough to save
            # and we've reached the chunk size limit
            if len(current_chunk) >= self.preferred_lines:
                # Save the current chunk
                self.chunks.append('\n'.join(current_chunk))
                self.metadata.append({
                    'file_path': relative_path,
                    'node_type': node_type,
                    'function_name': node_name if node_type in ['function', 'class'] else None,
                    'start_line': chunk_start_line,
                    'end_line': chunk_start_line + len(current_chunk) - 1
                })
                
                # Start a new chunk with configured overlap
                overlap_lines = max(1, len(current_chunk) * self.overlap_percentage // 100)
                current_chunk = current_chunk[-overlap_lines:] if overlap_lines > 0 else []
                chunk_start_line = chunk_start_line + len(current_chunk) - overlap_lines
        
        # Save the last chunk if it meets minimum size requirements
        chunk_content = '\n'.join(current_chunk)
        if current_chunk and len(current_chunk) >= self.min_lines:
            self.chunks.append(chunk_content)
            self.metadata.append({
                'file_path': relative_path,
                'node_type': node_type,
                'function_name': node_name if node_type in ['function', 'class'] else None,
                'start_line': chunk_start_line,
                'end_line': chunk_start_line + len(current_chunk) - 1
            })
    
    def get_indexed_chunks(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Get all indexed chunks and their metadata.
        
        Returns:
            Tuple of (chunks, metadata)
        """
        return self.chunks, self.metadata 