import os
import ast
from typing import List
from loguru import logger

# TODO: graph context for each keyworder as a graph

def get_imports(code: str) -> List[str]:
    """Extract all imports from a Python file."""
    try:
        tree = ast.parse(code)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(f"import {name.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                names = [n.name for n in node.names]
                imports.append(f"from {module} import {', '.join(names)}")
        return imports
    except Exception as e: #TODO: handle specific exceptions
        logger.error(f"Error extracting imports: {e}")
        return []

def extract_context(repo_path, keyword, max_lines=300):
    snippets = ""
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, 'r', errors='ignore') as f:
                    code = f.read()
                if keyword in code:
                    # Get imports first
                    imports = get_imports(code)
                    import_section = "\n".join(imports) if imports else "# No imports"
                    
                    # Get code snippet
                    code_lines = code.splitlines()[:max_lines]
                    # Remove imports from main code section to avoid duplication
                    code_lines = [line for line in code_lines 
                                if not line.strip().startswith(('import ', 'from '))]
                    snippet = "\n".join(code_lines)
                    
                    # Format to match prompt.py triple quote style
                    snippets += f"""
File: {path}

Code:
\"\"\"
{snippet}
\"\"\"

Dependencies:
\"\"\"
{import_section}
\"\"\"
"""
    return snippets.strip()
