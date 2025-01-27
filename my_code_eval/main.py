import sys
import os
import json
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

# Update path to point to src directory
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from py_coding_assistant.llms.base import LLMProviderType
from py_coding_assistant.llms.factory import LLMFactory
from py_coding_assistant.llms.dummy import DummyLLM
from tasks.SWE_bench_adapter import run_task_with_agent

class CodeGenerationAgent:
    """Agent that uses LLM for code generation"""
    def __init__(self, llm_provider: str = "dummy", model: str = None):
        if llm_provider == "dummy":
            self.llm = DummyLLM()
        else:
            self.llm = LLMFactory.create_llm(
                llm_provider=LLMProviderType(llm_provider),
                llm_model=model
            )
        
        # Set system prompt for code generation
        system_prompt = """You are a Python code generation assistant. 
        Generate only the code implementation without any explanations."""
        self.llm.set_system_prompt(system_prompt)

    def generate_code(self, prompt: str) -> str:
        """Generate code using the LLM"""
        response, _ = self.llm.generate_response(prompt)
        return response

def load_swe_bench_tasks(split: str = "dev") -> List[Dict[str, Any]]:
    """
    Load tasks from SWE-bench dataset, using local cache if available.
    
    Args:
        split: Which split to use ('dev', 'test', or 'train')
    Returns:
        List of tasks in standard format matching SWE-bench datum structure
    """
    splits = {
        'dev': 'data/dev-00000-of-00001.parquet',
        'test': 'data/test-00000-of-00001.parquet',
        'train': 'data/train-00000-of-00001.parquet'
    }
    
    if split not in splits:
        raise ValueError("Split must be one of: 'dev', 'test', 'train'")

    # Define paths
    data_dir = "data/swe-bench"
    os.makedirs(data_dir, exist_ok=True)
    local_path = os.path.join(data_dir, f"{split}.parquet")
    
    try:
        # Load from local cache if exists
        if os.path.exists(local_path):
            print(f"Loading {split} dataset from local cache")
            df = pd.read_parquet(local_path)
        else:
            print(f"Downloading {split} dataset from Hugging Face")
            # Download and save dataset
            remote_path = f"hf://datasets/princeton-nlp/SWE-bench/{splits[split]}"
            df = pd.read_parquet(remote_path)
            df.to_parquet(local_path)
        
        # Convert DataFrame rows to SWE-bench datum format
        tasks = []
        for _, row in df.iterrows():
            task = {
                "instance_id": row["instance_id"],
                "patch": row["patch"],
                "repo": row["repo"],
                "base_commit": row["base_commit"],
                "hints_text": row["hints_text"],
                "created_at": row["created_at"],
                "test_patch": row["test_patch"],
                "problem_statement": row["problem_statement"],
                "version": row["version"],
                "environment_setup_commit": row["environment_setup_commit"],
                "FAIL_TO_PASS": row["FAIL_TO_PASS"],
                "PASS_TO_PASS": row["PASS_TO_PASS"]
            }
            tasks.append(task)
        
        print(f"Loaded {len(tasks)} tasks from {split} split")
        return tasks
    
    except Exception as e:
        raise IOError(f"Failed to load dataset: {str(e)}")

def main():
    # Create agent with DummyLLM by default
    agent = CodeGenerationAgent(
        llm_provider="dummy",  # "dummy" uses DummyLLM directly
        model=None
    )
    
    # Alternatively, use Ollama:
    # agent = CodeGenerationAgent(
    #     llm_provider="ollama",
    #     model="codellama:7b"
    # )
    
    # Load tasks from Hugging Face
    tasks = load_swe_bench_tasks(split="dev")
    
    # Run evaluation
    results = []
    for task in tasks:
        print(f"Processing task {task['instance_id']}")
        result = run_task_with_agent(task, agent)
        results.append(result)
        
        # Print progress
        status = "✓" if result["success"] else "✗"
        print(f"{status} Task {task['instance_id']} - {result['iterations']} iterations")
    
    # Calculate and print metrics
    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r["success"])
    success_rate = successful_tasks / total_tasks
    
    print("\nEvaluation Results:")
    print(f"Total Tasks: {total_tasks}")
    print(f"Successful Tasks: {successful_tasks}")
    print(f"Success Rate: {success_rate:.2%}")
    
    # Create eval_results directory if it doesn't exist
    results_dir = "eval_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(results_dir, f"eval_results_{timestamp}.json")
    
    # Save detailed results
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    main() 