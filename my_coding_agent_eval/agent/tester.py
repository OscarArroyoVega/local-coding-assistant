import os
import subprocess
from loguru import logger

def run_tests(repo_path: str, conda_env_name: str) -> bool:
    """Run tests in the repository within the specified Conda environment."""
    try:
        # Construct the command to run pytest within the conda environment
        command = [
            "conda", "run", "-n", conda_env_name,
            "--no-capture-output", "--live-stream",
            "python", "-m", "pytest", "-q"
        ]

        logger.info(f"Running tests in Conda env '{conda_env_name}' with command: {' '.join(command)}")
        logger.info(f"Working directory: {repo_path}")

        # Run pytest within the conda environment
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )

        # Log test output
        if result.stdout:
            logger.debug(f"Test output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Test errors:\n{result.stderr}")

        if result.returncode != 0:
            logger.error(f"Tests failed in Conda env '{conda_env_name}' with return code {result.returncode}")
            return False
        else:
            logger.info(f"Tests passed in Conda env '{conda_env_name}'.")
            return True

    except FileNotFoundError:
        logger.error("'conda' command not found. Please ensure Conda/Miniconda is installed and in your PATH.")
        return False
    except Exception as e:
        logger.error(f"Failed to run tests in Conda env '{conda_env_name}': {str(e)}")
        return False
