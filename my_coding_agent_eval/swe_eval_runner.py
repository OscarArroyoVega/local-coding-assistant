import os, shutil, stat
from agent import (
    loader, repo_manager,
    context_builder as context,
    llm,
    docker_manager,
    diff_manager
    )
from loguru import logger

# --- Ensure Docker is available ---
if not docker_manager.is_docker_available():
    logger.error("Docker is required but not available. Exiting.")
    exit(1)

# --- Load Instance and Prepare Repo Path ---
instance = loader.load_instance()
repo = instance['repo']
commit = instance['base_commit']
issue_text = instance['problem_statement']
instance_id = instance['instance_id']
repo_path = os.path.join("repos", instance_id)
docker_image_tag = f"swe_eval_test_{instance_id.lower().replace('/','_')}" # Tag for the test image

# --- Clean existing repo (Windows-compatible) ---
def force_remove_readonly(func, path, _):
    # Add write permission and try removing again
    # Be careful with this function
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        logger.error(f"Error during force remove: {e}")

if os.path.exists(repo_path):
    logger.info(f"Removing existing repo at {repo_path}")
    shutil.rmtree(repo_path, ignore_errors=False, onerror=force_remove_readonly)

# --- Clone and Checkout ---
if not repo_manager.clone_and_checkout(repo, commit, repo_path):
     logger.error(f"Failed to clone or checkout {repo} at {commit}. Exiting.")
     exit(1)

# --- LLM Interaction and Patch Application (On Host) ---
apply_success = False
try:
    # Generate context
    keywords = ["def", "class"]
    ctx = ""
    if os.path.exists(repo_path):
        for keyword in keywords:
             ctx_part = context.extract_context(repo_path, keyword)
             if ctx_part: ctx += f"\n\n{ctx_part}"
    else:
        logger.error(f"Repo path {repo_path} does not exist before context extraction.")
        raise FileNotFoundError(f"Repo path {repo_path} missing.")

    # Initialize LLM
    llm_interface = llm.LLMInterface(api_key="your-api-key", model="qwen2.5-coder:7b") # Replace with actual key loading

    # Generate file content
    target_file = "test.py" # Placeholder - Determine dynamically
    new_content = llm_interface.generate_file(repo_path, target_file, issue_text, ctx)

    if not new_content:
        logger.error("❌ LLM failed to generate file content")
        apply_success = False # Treat as failure if no content generated
    else:
        logger.info(f"LLM generated new content for {target_file}")
        # Apply changes
        full_path = os.path.join(repo_path, target_file)
        try:
            file_diff = diff_manager.apply_changes(full_path, new_content)
            logger.info(f"Applied changes to {target_file}")
            logger.debug(f"File diff:\n{file_diff}")
            apply_success = True # Mark apply as successful
        except Exception as e:
            logger.error(f"❌ Failed to apply changes to {target_file}: {str(e)}")
            apply_success = False

except Exception as e:
    logger.error(f"❌ Error during LLM generation or patch application phase: {str(e)}")
    apply_success = False


# --- Build Env & Run Tests in Docker ---
tests_success = False
if apply_success:
    logger.info("--- Building test environment in Docker ---")
    # Build image containing repo code and environment (based on env files found)
    build_success = docker_manager.build_image_for_repo(repo_path, docker_image_tag)    

    if build_success:
        logger.info(f"✅ Docker image {docker_image_tag} built successfully.")
        logger.info("--- Running tests in Docker ---")
        # Define the command to run tests inside the container
        # This might need adjustment based on the repo's test setup
        test_command = ["python", "-m", "pytest"]
        test_exit_code, test_logs = docker_manager.run_command_in_container(
            docker_image_tag, test_command, repo_path
        )

        if test_exit_code == 0:
            logger.info("✅ Tests passed successfully in Docker container.")
            tests_success = True
        else:
            logger.error(f"❌ Tests failed in Docker container with exit code {test_exit_code}.")
            # Log only a portion of logs initially, can increase verbosity if needed
            log_snippet = (test_logs[:1000] + '...') if len(test_logs) > 1000 else test_logs
            logger.error(f"Test logs (snippet):\n{log_snippet}")
            tests_success = False
    else:
        logger.error(f"❌ Docker image build failed. Skipping tests.")
        tests_success = False
else:
     logger.warning("Skipping build and test steps because patch application failed.")

# --- Clean up ---
# Optional: Remove the Docker image
docker_manager.cleanup_image(docker_image_tag)

# Final result
if apply_success and tests_success:
    logger.info("✅✅✅ Evaluation SUCCESS!")
else:
    logger.info("❌❌❌ Evaluation FAILED.")
    # Add reasons
    if not apply_success: logger.info("Reason: Patch application failed.")
    elif not tests_success: logger.info("Reason: Docker image build or tests failed.")
