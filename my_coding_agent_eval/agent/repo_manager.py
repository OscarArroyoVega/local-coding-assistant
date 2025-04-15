import os, subprocess

def clone_and_checkout(repo_slug, commit_sha, local_path):
    repo_url = f"https://github.com/{repo_slug}.git"
    if not os.path.exists(local_path):
        subprocess.run(["git", "clone", repo_url, local_path], check=True)
    subprocess.run(["git", "checkout", commit_sha], cwd=local_path, check=True)

def apply_patch(patch_text, repo_path, filename="suggested.patch"):
    patch_file = os.path.join(repo_path, filename)
    with open(patch_file, "w") as f:
        f.write(patch_text)
    result = subprocess.run(["git", "apply", patch_file], cwd=repo_path, check=True)
    return result.returncode == 0