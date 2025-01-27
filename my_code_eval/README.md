# eval-code-assistant

This is a tool to evaluate the performance of a code assistant.

It uses the SWE-bench dataset and the test runner to evaluate the performance of the code assistant.

in this first attempt: 
1:  we use a task adapter to convert the SWE-bench dataset into a format that 
    can be used by the code assistant in a loop for all the instances in the dataset.

2: we use a test runner to test the generated code against the test cases.

3: we log the results of the test runner.

next:
- call a model builder to build a model that can be used to evaluate the performance of the code assistant.
- prepare the tests to be run in a loop for all the instances in the dataset.
- add metrics to the evaluation.(number of tokens, time, etc)

TODO check https://github.com/Aider-AI/aider-swe-bench/tree/main for a more consistent approach, valid for benchmark purposes against other agents.
