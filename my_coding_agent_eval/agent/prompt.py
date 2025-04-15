def create_prompt(repo: str, issue_text: str, code_context: str = None) -> str:
    """Create a structured prompt for the LLM."""

    prompt = f"""You are an AI coding assistant. A GitHub issue is reported for the repository {repo}.

        Issue Description:
        \"\"\"
        {issue_text}
        \"\"\"
        """
            
            # Add code context if provided
    if code_context:
        prompt += f"""\n\nRelevant Code Context:
        \"\"\"
        {code_context}
        \"\"\"
        """
        
    # Add labeled examples
    prompt += f"""\n\nThe response should be a valid unified diff patch. Follow the structure and style shown in the example patches below. without any additional text.
        \"\"\"
        correct response Example 1:
        diff --git a/utils.py b/utils.py
        --- a/utils.py
        +++ b/utils.py
        @@ def normalize(data):
        -    return (data - data.min()) / data.max()
        +    return (data - data.min()) / (data.max() - data.min())
        \"\"\"
        \"\"\"
        correct response Example 2:
        diff --git a/downloader.py b/downloader.py
        --- a/downloader.py
        +++ b/downloader.py
        @@ def download_file(url):
        -    response = requests.get(url)
        -    return response.content
        +    try:
        +        response = requests.get(url, timeout=5)
        +        response.raise_for_status()
        +        return response.content
        +    except requests.RequestException as e:
        +        print(f"Download failed")
        +        return None
        \"\"\"


        \"\"\"
        correct response Example 3:
        diff --git a/train.py b/train.py
        --- a/train.py
        +++ b/train.py
        @@ def train_model(data):
        -    for d in data:
        -        result = process(d)
        +    for sample in data:
        +        result = process(sample)
        \"\"\"


        \"\"\"
        incorrect response Example 1:
        Here is the patch that fixes the issue:
        diff --git a/utils.py b/utils.py
        --- a/utils.py
        +++ b/utils.py
        @@ def normalize(data):
        -    return (data - data.min()) / data.max()
        \"\"\"
        
        \"\"\"
        incorrect response Example 2:
        Here is the fix for your code examples as an Unified Diff (UdD):
        ```diff
        --- a/utils.py
        +++ b/utils.py
        @@ -1 +1 @@ 
        -return data / max_data;
        +return ((data * min_max) - min_val) / range_;
        --- a/downloader.py
        +++ b/downloader.py
        \"\"\"        
        
        \"\"\"
        incorrect response Example 3:
        The patch that fixes the issue is:
        diff --git a/train.py b/train.py
        --- a/train.py
        +++ b/train.py
        @@ def train_model(data):
        -    for d in data:
        -        result = process(d)
        \"\"\"
        """

    prompt += f"""\n\nProvide a fix as a valid unified diff patch.
        \"\"\"
        - IMPORTANT: Output only a valid unified diff.
        - DO NOT include any explanation, markdown formatting, or extra text.
        - The diff must exactly match the file context; do not alter context lines.
        \"\"\"
        """
    
    return prompt