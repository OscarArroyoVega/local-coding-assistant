def extract_diff(raw_patch):
    lines = raw_patch.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("diff --git"):
            return "\n".join(lines[i:]).strip()
    return ""

def normalize_patch(diff):
    return "\n".join(line.rstrip() for line in diff.splitlines())


   




