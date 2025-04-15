import docker
import os
import io
import uuid
from docker.errors import BuildError, APIError, ImageNotFound, NotFound
from docker.types import Mount
from loguru import logger

# --- Docker Client Initialization ---
try:
    client = docker.from_env()
    client.ping() # Check connection
    logger.info("Docker client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Docker client: {e}")
    logger.error("Please ensure Docker Desktop is running and accessible.")
    client = None # Indicate client is not available

def is_docker_available() -> bool:
    """Check if the Docker client is available."""
    return client is not None

# --- Dockerfile Generation ---
def generate_dockerfile(repo_path: str, base_image: str = "python:3.9-slim") -> tuple[str | None, str | None]:
    """Generates Dockerfile content based on environment files found in repo_path."""

    env_file_path_host = os.path.join(repo_path, "environment.yml")
    conda_env_name = "testenv" # Name for the environment inside the container

    dockerfile_content = f"""
FROM {base_image}

# Install git, conda (via miniforge), build tools
RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    ca-certificates \\
    build-essential \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install Conda via Miniforge
RUN curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" && \\
    bash Miniforge3-$(uname)-$(uname -m).sh -b -p /opt/conda && \\
    rm Miniforge3-$(uname)-$(uname -m).sh

# Set PATH to include conda
ENV PATH="/opt/conda/bin:${{PATH}}"

# Set up a working directory for the code
WORKDIR /workspace
COPY . /workspace

# Environment setup logic
"""

    env_setup_commands = ""
    detected_env_type = None

    # Strategy 1: Use environment.yml if it exists
    if os.path.exists(env_file_path_host):
        logger.info("Found environment.yml, will use Conda for environment setup.")
        detected_env_type = "conda"
        env_setup_commands = f"""
RUN conda env create -n {conda_env_name} -f environment.yml || conda env update -n {conda_env_name} -f environment.yml
# Activate conda environment for subsequent RUN/CMD commands
SHELL ["conda", "run", "-n", "{conda_env_name}", "/bin/bash", "-c"]

# Install the package itself in editable mode within the conda env
RUN pip install --no-deps -e .
"""
    # Strategy 2: Check for pyproject.toml setup
    elif os.path.exists(os.path.join(repo_path, "pyproject.toml")):
        logger.warning("No environment.yml found. Checking for pyproject.toml setup.")
        detected_env_type = "pip"
        env_setup_commands = f"""
# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install build dependencies with specific versions
RUN pip install --no-cache-dir \\
    "setuptools==57.5.0" \\
    "wheel>=0.40.0" \\
    "pytest>=8.0.0" \\
    "setuptools_scm<8.0.0" \\
    --upgrade pip

# Print key package versions for debugging
RUN pip freeze | grep -E 'setuptools==|setuptools-scm==|pytest==|pip==' || echo "Key packages not found"

# Create a requirements.txt file that pins setuptools
RUN echo "setuptools==57.5.0" > /tmp/requirements.txt

# Install the package in editable mode with specific pip options
RUN pip install -e . \\
    --no-build-isolation \\
    -r /tmp/requirements.txt \\
    --config-settings=editable-mode=compat
"""
    # Strategy 3: Basic pip install if no environment.yml or pyproject.toml
    else:
        logger.warning("No environment.yml or pyproject.toml found. Attempting basic pip install with build deps.")
        detected_env_type = "pip"
        env_setup_commands = f"""
# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# First install an older setuptools that has dep_util
RUN pip install --no-cache-dir "setuptools==57.5.0"

# Then install other build dependencies
RUN pip install --no-cache-dir \\
    "wheel>=0.40.0" \\
    "pytest>=8.0.0" \\
    "setuptools_scm<8.0.0" \\
    --upgrade pip

# Print key package versions for debugging
RUN pip freeze | grep -E 'setuptools==|setuptools-scm==|pytest==|pip==' || echo "Key packages not found"

# Install the package in editable mode with the older setuptools
RUN pip install -e .
"""

    dockerfile_content += env_setup_commands
    dockerfile_content += """
# Set default command or entrypoint if needed, or rely on run command
# CMD ["pytest"]
"""
    return dockerfile_content, detected_env_type


# --- Docker Operations ---
def build_image_for_repo(repo_path: str, tag: str) -> bool:
    """Builds a Docker image specific to the repo using a generated Dockerfile."""
    if not is_docker_available(): return False

    # Define temporary Dockerfile path *within* the repo context
    temp_dockerfile_path = os.path.abspath(os.path.join(repo_path, ".dockerfile_generated"))
    dockerfile_content, _ = generate_dockerfile(repo_path)

    if not dockerfile_content:
        logger.error("Failed to generate Dockerfile content.")
        return False

    logger.info(f"Building Docker image with tag: {tag} from path: {repo_path}")
    logger.debug(f"Using temporary Dockerfile: {temp_dockerfile_path}")

    try:
        # Write the generated Dockerfile content to the temporary file
        with open(temp_dockerfile_path, "w") as f:
            f.write(dockerfile_content)

        # Build the image using the repo path as context and specifying the created Dockerfile
        logger.info(f"Starting docker build...")
        image, build_log_stream = client.images.build(
            path=repo_path,                    # Build context is the repo directory
            dockerfile=temp_dockerfile_path,   # Specify our generated Dockerfile
            tag=tag,
            rm=True,                           # Remove intermediate containers
            forcerm=True                       # Force removal
        )
        logger.info(f"Docker build command initiated for image: {tag}")

        # Process the build log stream
        last_log_line = None
        for line in build_log_stream:
            if 'stream' in line:
                log_line = line['stream'].strip()
                if log_line: # Avoid logging empty lines
                     logger.debug(f"Build log: {log_line}")
                     last_log_line = log_line # Keep track of the last line for potential error reporting
            elif 'errorDetail' in line:
                error_detail = line['errorDetail']
                logger.error(f"Build Error Detail: {error_detail.get('message')}")
                # Re-raise or handle specific build errors based on 'errorDetail' if needed
                # For now, we rely on the final status check or exceptions below

        # Verify image exists after build attempt (build() might return before stream ends on error)
        try:
             client.images.get(tag)
             logger.info(f"Successfully built image: {tag}")
             return True
        except ImageNotFound:
             logger.error(f"Docker image build failed for tag {tag}. Image not found after build.")
             # Log the last known log line if available
             if last_log_line:
                  logger.error(f"Last build log line before failure: {last_log_line}")
             return False


    except BuildError as e: # Catch explicit BuildError from docker-py if raised
        logger.error(f"Docker BuildError exception for tag {tag}: {e}")
        # Log detailed build output from the exception if available
        if e.build_log:
             for line in e.build_log:
                  if 'stream' in line:
                       logger.error(f"Build log (exception): {line['stream'].strip()}")
        return False
    except APIError as e:
        logger.error(f"Docker API error during build: {e}")
        return False
    except TypeError as e:
         # Catch potential TypeError from build args, e.g., path issue
         logger.error(f"TypeError during docker build setup: {e}")
         return False
    except Exception as e:
        logger.error(f"Unexpected error during Docker build: {type(e).__name__}: {e}")
        return False
    finally:
        # Clean up the temporary Dockerfile
        if os.path.exists(temp_dockerfile_path):
            try:
                os.remove(temp_dockerfile_path)
                logger.debug(f"Removed temporary Dockerfile: {temp_dockerfile_path}")
            except OSError as e:
                logger.warning(f"Could not remove temporary Dockerfile {temp_dockerfile_path}: {e}")


def run_tests_in_container(image_tag: str, test_command: list = ["python", "-m", "pytest"]) -> tuple[int, str]:
    """Runs the test command inside a new Docker container using the pre-built image."""
    if not is_docker_available(): return -1, "Docker client not available."

    # No mount needed if build context was repo_path and image includes code+env
    # If changes were made *after* build, mount would be needed. Assuming build is final step before test.
    container_name = f"test_runner_{image_tag}_{uuid.uuid4().hex[:6]}"
    logger.info(f"Running tests in container {container_name} (image: {image_tag}): {' '.join(test_command)}")

    container = None
    try:
        container = client.containers.run(
            image=image_tag,
            command=test_command,
            name=container_name,
            detach=True,
            # No working_dir needed if WORKDIR /workspace is set and code is there
        )

        result = container.wait(timeout=1800) # 30 min timeout for tests
        exit_code = result.get('StatusCode', -1)
        logs = container.logs().decode('utf-8', errors='replace') # Handle potential encoding errors

        logger.info(f"Test command completed with exit code: {exit_code}")
        return exit_code, logs

    except APIError as e:
        logger.error(f"Docker API error running tests: {e}")
        return -1, f"Docker API error: {e}"
    except Exception as e:
        logger.error(f"Unexpected error running tests in container: {e}")
        return -1, f"Unexpected error: {e}"
    finally:
        if container:
            try:
                container.stop(timeout=10)
                container.remove()
                logger.info(f"Test container {container.name} removed.")
            except NotFound: pass # Already gone
            except APIError as e: logger.error(f"API error removing test container {container.name}: {e}")
            except Exception as e: logger.error(f"Error removing test container {container.name}: {e}")

def cleanup_image(tag: str):
    """Removes a Docker image by tag."""
    if not is_docker_available(): return
    logger.info(f"Attempting to remove Docker image: {tag}")
    try:
        client.images.remove(image=tag, force=True)
        logger.info(f"Successfully removed image: {tag}")
    except ImageNotFound: logger.warning(f"Image {tag} not found for removal.")
    except APIError as e: logger.error(f"API error removing image {tag}: {e}")
    except Exception as e: logger.error(f"Unexpected error removing image {tag}: {e}")
