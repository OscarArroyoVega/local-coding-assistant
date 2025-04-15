import os, subprocess
from loguru import logger

def clone_and_checkout(repo_slug, commit_sha, local_path):
    repo_url = f"https://github.com/{repo_slug}.git"
    try:
        if not os.path.exists(local_path):
            logger.info(f"Cloning {repo_url} into {local_path}...")
            subprocess.run(["git", "clone", repo_url, local_path], check=True, capture_output=True, text=True)
        logger.info(f"Checking out commit {commit_sha} in {local_path}...")
        subprocess.run(["git", "checkout", commit_sha], cwd=local_path, check=True, capture_output=True, text=True)
        logger.info(f"Successfully cloned/checked out.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {' '.join(e.cmd)}")
        logger.error(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during clone/checkout: {e}")
        return False

def apply_patch(patch_text, repo_path, filename="suggested.patch"):
    patch_file = os.path.join(repo_path, filename)
    try:
        with open(patch_file, "w") as f:
            f.write(patch_text)
        logger.info(f"Applying patch file {patch_file}...")
        result = subprocess.run(
            ["git", "apply", "--check", patch_file],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.warning(f"git apply --check failed. Patch may not apply cleanly. Stderr:\n{result.stderr}")
        result_apply = subprocess.run(
             ["git", "apply", patch_file],
             cwd=repo_path,
             capture_output=True,
             text=True
        )
        if result_apply.returncode != 0:
             logger.error(f"git apply failed. Stderr:\n{result_apply.stderr}")
             return False
        else:
             logger.info(f"Patch applied successfully.")
             return True
    except IOError as e:
         logger.error(f"Failed to write patch file {patch_file}: {e}")
         return False
    except subprocess.CalledProcessError as e:
        logger.error(f"git apply command failed unexpectedly: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during apply_patch: {e}")
        return False
    finally:
        if os.path.exists(patch_file):
            try:
                os.remove(patch_file)
            except OSError as e:
                logger.warning(f"Could not remove temporary patch file {patch_file}: {e}")