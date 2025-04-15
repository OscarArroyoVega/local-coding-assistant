import os
from typing import Optional
from loguru import logger

def apply_changes(file_path: str, content: str) -> str:
    """Apply changes to a file and return the diff."""
    try:
        # Normalize path for Windows
        file_path = os.path.normpath(file_path)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Read existing content if file exists
        old_content = ""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                old_content = f.read()
        
        # Write new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Generate diff
        diff = generate_diff(old_content, content)
        return diff
        
    except Exception as e:
        logger.error(f"Failed to apply changes to {file_path}: {str(e)}")
        raise

def generate_diff(old_content: str, new_content: str) -> str:
    """Generate a diff between old and new content."""
    from difflib import unified_diff
    
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    diff = list(unified_diff(
        old_lines,
        new_lines,
        fromfile='old',
        tofile='new',
        lineterm=''
    ))
    
    return '\n'.join(diff)

def read_file(file_path: str) -> Optional[str]:
    """Read the content of a file."""
    try:
        # Normalize path for Windows
        file_path = os.path.normpath(file_path)
        
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {str(e)}")
        return None 