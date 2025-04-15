# how to EVAL our code-assistant

This is a tool to evaluate the performance of a code assistant.

We will use the SWE-bench-lite (300 issues) dataset to make it computational accessible. 
SWE-bench Lite is a subset of SWE-bench that's been curated to make evaluation less costly and more accessible.
For more info [swebench.com](https://swebench.com)


## 1 Generate our LLM Agent predictions
Given an issue (problem_statement) + codebase (repo + base_commit), our model should attempt to write a diff patch prediction.

So we need to generate predictions in this format: 

```json
{
    "instance_id": "<Unique task instance ID>",
    "model_patch": "<.patch file content string>",
    "model_name_or_path": "<Model name here (i.e. SWE-Llama-13b)>",
}
```

and store them in a .json file formated as:
```json
[<prediction 1>,<prediction 2>,...<prediction n>]
```

To to this, or each instance of the tasks in the dataset

#### 0 download the dataset 

#### 1 Clone the Repository at the Base Commit (URL provided in the dataset)

```python
import subprocess, os

inst = dataset[0]  # example first task
repo_url = f"https://github.com/{inst['repo']}.git"
repo_dir = os.path.join("repos", inst["instance_id"])
subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
subprocess.run(["git", "checkout", inst["base_commit"]], cwd=repo_dir, check=True)
```
This will create a working copy of the code for the issue. The codebase plus issue description is the input context for the mode.

#### 2 Generate a Fix with the LLM Agent

we will generate a patch taht modifies the repository to fix the output.

```python
issue_text = inst["problem_statement"]
# (Optional) You might extract certain files or hints from inst to assist the model.
proposed_fix = my_llm_agent.generate_patch(issue_text, repo_dir)
```

if the result is not a diff, but a code snippet (function body or code block) we will need to integrate it into a patch format.

#### 3 (optional) convert code snippets to Diffs

```python
# Suppose proposed_fix is a code snippet and we know it belongs in file_x.py at function foo()
apply_snippet_to_file(proposed_fix, file_path="path/to/file_x.py")  # pseudo-function
# Now create a diff against the base commit:
diff_output = subprocess.check_output(
    ["git", "-C", repo_dir, "diff", inst["base_commit"]]
).decode("utf-8")
```
#### 4 Collect predictions in the required format
```python
predictions = []
for inst in dataset:
    instance_id = inst["instance_id"]
    # ... run agent to get patch ...
    model_patch = proposed_fix  # ensure this is a diff string
    pred = {
        "instance_id": instance_id,
        "model_patch": model_patch,
        "model_name_or_path": "MyLLM-Agent"
    }
    predictions.append(pred)
# Save to file:
import json
with open("predictions.json", "w") as f:
    json.dump(predictions, f)
```


## 2 Evaluate our results

#### 1 Install SWE-bench

```bash
pip install swebench
```

or install it from source

```bash
pip install https://github.com/princeton-nlp/SWE-bench.git
```

or build it from source.

```bash
git clone https://github.com/princeton-nlp/SWE-bench.git
cd SWE-bench
pip install -e .
```

#### 2 loac the Task Data

``` python
from datasets import load_dataset

dataset = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')
print(f"Loaded {len(dataset)} tasks")
# Each item in 'dataset' is a dict with fields like instance_id, repo, base_commit, etc.
```

#### 3 evaluate patch predictions on SWE-bench Lite

``` python 
-m swebench.harness.run_evaluation \
--dataset_name princeton-nlp/SWE-bench_Lite \
--predictions_path <path_to_predictions> \
--max_workers <num_workers> \
--run_id <run_id>
# use --predictions_path 'gold' to verify the gold patches
# use --run_id to name the evaluation run
```

This command will generate docker build logs (logs/build_images) and evaluation logs (logs/run_evaluation) in the current directory.

The final evaluation results will be stored in the evaluation_results directory.



### References

@inproceedings{
    jimenez2024swebench,
    title={{SWE}-bench: Can Language Models Resolve Real-world Github Issues?},
    author={Carlos E Jimenez and John Yang and Alexander Wettig and Shunyu Yao and Kexin Pei and Ofir Press and Karthik R Narasimhan},
    booktitle={The Twelfth International Conference on Learning Representations},
    year={2024},
    url={https://openreview.net/forum?id=VTF8yNQM66}
}


my_coding_agent_eval/
├── agent/
│   ├── __init__.py
│   ├── loader.py          # Load SWE-bench instances
│   ├── repo_manager.py    # Clone repo, checkout commit, apply patches
│   ├── context.py         # Extract code context for LLM
│   ├── llm.py             # Interface to Ollama
│   ├── patch.py           # Clean and apply LLM-generated patches
│   └── tester.py          # Run tests and check results
├── swe_eval_runner.py     # Main script to run the agent
├── requirements.txt
└── README.md
