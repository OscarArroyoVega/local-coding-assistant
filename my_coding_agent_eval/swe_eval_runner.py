import os, shutil, stat, subprocess, tempfile
from agent import loader, repo_manager, context, llm, patch, tester, prompt
from loguru import logger

instance = loader.load_instance()
repo = instance['repo']
commit = instance['base_commit']
issue_text = instance['problem_statement']
instance_id = instance['instance_id']
repo_path = os.path.join("repos", instance_id)

# --- Clean existing repo (Windows-compatible)
def force_remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

if os.path.exists(repo_path):
    print(f"Removing existing repo at {repo_path}")
    shutil.rmtree(repo_path, onerror=force_remove_readonly)

repo_manager.clone_and_checkout(repo, commit, repo_path)
keywords = ["def", "class"]
ctx = ""
for keyword in keywords: #clone and checkout the repo
    ctx += f"\n\n{context.extract_context(repo_path, keyword)}"  # crude context
    #generate prompt
prompt = prompt.create_prompt(repo, issue_text, ctx)
logger.debug(f"Prompt:\n{prompt}")

raw_patch = llm.generate_patch(prompt, model="qwen2.5-coder:7b")
logger.info(f"Raw patch from LLM:\n{raw_patch[:500]}")
diff = patch.extract_diff(raw_patch)
if not diff:
    logger.info("❌ Failed to extract diff.")
    exit(1)
logger.info(f"Extracted diff:\n{diff[:500]}")
diff = patch.normalize_patch(diff)
# Write the diff to a temporary file
with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.patch') as temp_patch_file:
    temp_patch_file.write(diff)
    temp_patch_file_path = temp_patch_file.name

try:
    # Apply the patch using the temporary file
    success = subprocess.run(["git", "apply", temp_patch_file_path], cwd=repo_path, check=True)
    logger.debug(f"Apply patch result: {success}")
finally:
    # Clean up the temporary file
    os.remove(temp_patch_file_path)

tests_success = tester.run_tests(repo_path)
logger.debug(f"Tests result: {tests_success}")
if success and tests_success:
    logger.info("✅ Success!")
else:
    logger.info("❌ Failed.")
