import os
from typing import Optional

def create_prompt(repo_path: str, target_file: str, issue_description: str, context: str = None) -> str:
    """Create a prompt for file generation based on the issue description and context."""
    # Get the file extension to determine the language
    file_ext = os.path.splitext(target_file)[1].lower()
    
    # Map file extensions to languages
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.sh': 'Shell',
        '.md': 'Markdown',
        '.html': 'HTML',
        '.css': 'CSS',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.xml': 'XML',
        '.sql': 'SQL',
        '.dockerfile': 'Dockerfile',
        '.dockerignore': 'Dockerignore',
        '.gitignore': 'Gitignore',
        '.env': 'Environment Variables',
        '.ini': 'INI',
        '.toml': 'TOML',
        '.csv': 'CSV',
        '.txt': 'Text',
    }
    
    language = language_map.get(file_ext, 'Unknown')
    
    # Incorporate Context into the prompt
    context_section = ""
    if context:
        context_section = f"""
Relevant Code Context:
--- START CONTEXT ---
{context}
--- END CONTEXT ---
"""
    
    # Create the prompt, including the context section if available
    prompt = f"""You are a professional software developer. Your task is to generate a complete {language} file based on the following requirements and context:

File: {target_file}
Language: {language}
{context_section}
Requirements:
{issue_description}

Please generate the complete file content. Use the provided Code Context for reference if necessary. Include all necessary imports, dependencies, and code structure. The code should be well-formatted, documented, and follow best practices for {language} development.

Return only the complete file content, without any additional explanations or markdown formatting."""

    return prompt.strip() # Use strip() to remove leading/trailing whitespace