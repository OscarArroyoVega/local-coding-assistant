import os
from typing import Optional
from loguru import logger
from .prompt import create_prompt
from .diff_manager import apply_changes, generate_diff

class LLMInterface:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    def generate_file(self, repo_path: str, target_file: str, issue_description: str, context: str = None) -> Optional[str]:
        """Generate a complete file based on the issue description and context."""
        try:
            # Create the prompt for file generation, passing the context
            # Assuming create_prompt accepts context as the 4th argument
            prompt = create_prompt(repo_path, target_file, issue_description, context) # Pass context here

            # Call the API to generate the file content
            response = self._call_api(prompt)

            if not response:
                logger.error("Failed to generate file content")
                return None

            # !! Important Change: This function should return the NEW FILE CONTENT,
            # !! not the diff. Applying changes happens later in the runner.
            # full_path = os.path.join(repo_path, target_file)
            # diff = apply_changes(full_path, response) # Moved to runner
            # return diff
            return response # Return the generated content directly

        except Exception as e:
            logger.error(f"Error generating file: {str(e)}")
            return None

    def _call_api(self, prompt: str) -> Optional[str]:
        """Make the actual API call to generate the file content."""
        # This is a placeholder - implement actual API call
        # Return the complete file content as a string
        logger.info("Calling LLM API (placeholder)...")
        logger.debug(f"Prompt:\n{prompt}")
        # Replace placeholder with actual API call using self.api_key and self.model
        generated_content = f"# Generated content based on issue\n# Target file: {prompt.split('File: ')[1].split('\\n')[0]}\n\ndef example_function():\n    # TODO: Implement logic based on prompt\n    print(\"Placeholder implementation\")\n    return True\n"
        logger.info("LLM API call completed (placeholder).")
        return generated_content # Placeholder return
