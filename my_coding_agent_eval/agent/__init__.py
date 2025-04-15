"""
Agent package for coding agent evaluation.
"""

from .llm import LLMInterface
from .diff_manager import apply_changes, generate_diff, read_file
from .prompt import create_prompt
from .patch_manager import extract_diff, normalize_patch, sanitize_diff, adjust_hunk_header, get_target_files
from .repo_manager import clone_and_checkout
from .context_builder import extract_context
from .tester import run_tests
from .loader import load_instance


__all__ = [
    'LLMInterface',
    'apply_changes',
    'generate_diff',
    'read_file',
    'create_prompt',
    'extract_diff',
    'normalize_patch',
    'sanitize_diff',
    'adjust_hunk_header',
    'get_target_files',
    'clone_and_checkout',
    'extract_context',
    'run_tests',
    'load_instance',
    'build_image'
] 