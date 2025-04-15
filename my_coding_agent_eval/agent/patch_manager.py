import re
import os

def extract_diff(raw_llm_output: str) -> str:
    """
    Extracts the diff block from raw LLM output,
    handling optional markdown code fences (```diff ... ```)
    and looking for standard diff starting lines.
    Removes any trailing markdown fences.
    Returns an empty string if no diff is found.
    """
    if not raw_llm_output:
        return ""

    cleaned_output = raw_llm_output.strip()

    # 1. Try to extract diff from markdown fences
    # This regex allows for optional spaces and handles different newline variants.
    fence_match = re.search(r"```diff\s*\n(.*?)\n```", cleaned_output, re.DOTALL)
    if fence_match:
        diff_text = fence_match.group(1).strip()
        # Check if the content looks like a diff
        if diff_text.startswith("diff --git") or diff_text.startswith("--- "):
            return diff_text

    # 2. If no valid fenced diff is found, search the entire text for lines that start like a diff.
    lines = cleaned_output.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("diff --git") or line.startswith("--- "):
            potential_diff = "\n".join(lines[i:]).strip()
            # Remove a trailing markdown fence if present (e.g., an extra "```" at the end)
            potential_diff = re.sub(r"\n```$", "", potential_diff)
            return potential_diff

    # 3. Return empty if nothing matching a diff block is found.
    return ""

def normalize_patch(diff: str) -> str:
    """
    Normalizes a patch string by removing any trailing whitespace
    from each line.
    """
    return "\n".join(line.rstrip() for line in diff.splitlines())

def sanitize_diff(diff: str) -> str:
    """
    Cleans the diff header lines by removing extra metadata,
    such as trailing text after a tab or multiple spaces.
    For example, converts:
      --- repos/astropy__astropy-11693/examples/io/create-mef.py      (revision 12345)
    to:
      --- repos/astropy__astropy-11693/examples/io/create-mef.py
    """
    lines = diff.splitlines()
    sanitized_lines = []
    for line in lines:
        # Only sanitize header lines (those starting with '--- ' or '+++ ')
        if line.startswith('--- ') or line.startswith('+++ '):
            # Remove any trailing tab characters or multiple spaces and following text.
            sanitized_line = re.sub(r'(\t|\s{2,}).*$', '', line)
            sanitized_lines.append(sanitized_line)
        else:
            sanitized_lines.append(line)
    # Ensure the diff ends with a newline
    return "\n".join(sanitized_lines) + "\n"
def adjust_hunk_header(hunk_header: str, target_file: str) -> str:
    """
    Given a hunk header and the target file, search the file for the first occurrence 
    of the context line after the reported starting line. Return an updated header if needed.
    """
    # Parse the hunk header
    m = re.match(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@ (.*)", hunk_header)
    if not m:
        return hunk_header  # unexpected format, so leave it

    orig_line, orig_count, new_line, new_count, context_line = m.groups()
    orig_line = int(orig_line)
    # Read the file content into a list of lines
    with open(target_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Search for context_line starting at the reported orig_line index (adjust for 0-index)
    for i in range(orig_line - 1, len(lines)):
        if context_line.strip() in lines[i]:
            correct_line = i + 1  # line numbers start at 1
            if correct_line != orig_line:
                # Reconstruct hunk header with the corrected number
                new_hunk_header = f"@@ -{correct_line},{orig_count} +{new_line},{new_count} @@ {context_line}"
                return new_hunk_header
            break

    return hunk_header  # if nothing changed, return as-is


def get_target_files(diff_text: str) -> list[str]:
    """
    Parses a git diff string and extracts the target file paths.
    Strips potential 'repos/<instance_id>/' prefix.
    Handles paths like --- a/path/to/file.py or --- /dev/null
    """
    target_files = set()
    # Regex to find lines starting with --- or +++ followed by a path
    # Handles 'a/' prefix and paths starting with '/' or directly with filename
    pattern = re.compile(r"^(?:---|\+\+\+) (?:a\/|b\/)?(.+?)(?:\t.*)?$")
    # Regex to capture the 'repos/instance_id/' prefix if present
    prefix_pattern = re.compile(r"^repos\/[^\/]+\/(.*)")

    for line in diff_text.splitlines():
        match = pattern.match(line)
        if match:
            filepath = match.group(1).strip()
            # Check for and strip the prefix
            prefix_match = prefix_pattern.match(filepath)
            if prefix_match:
                filepath = prefix_match.group(1) # Use the part after the prefix
            # Ignore /dev/null which indicates a new or deleted file, not a missing one
            if filepath != "/dev/null":
                target_files.add(filepath)
    return list(target_files)


   




