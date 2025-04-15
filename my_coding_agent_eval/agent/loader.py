from datasets import load_dataset

def load_instance(index=1):
    dataset = load_dataset('princeton-nlp/SWE-bench', split='test')
    print(len(dataset))
    print(dataset[index])
    # Retrieve one instance (as an example)
    instance = dataset[index]
    print(instance.keys())
    # Example keys: ['repo', 'instance_id', 'base_commit', 'problem_statement', 'patch', 'test_patch', ...]

    return instance
