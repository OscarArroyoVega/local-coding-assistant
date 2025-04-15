import requests, json

def generate_patch(prompt, model="qwen2.5-coder:7b", url="http://localhost:11434/api/generate"):
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {"temperature": 0.2},
        "stream": False
    } 
    timeout = 300
    res = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=timeout)
    return res.json().get("response", "").strip()
