import subprocess

def run_tests(repo_path):
    result = subprocess.run(["pytest", "-q"], cwd=repo_path)
    return result.returncode == 0
