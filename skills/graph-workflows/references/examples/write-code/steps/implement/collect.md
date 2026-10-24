# Collect and integrate the implementation

Given Work with a handle or completed result for every package, Assignments, Task, Repository, project instructions, Plan, PR context, and any Failure evidence, obtain the outcome of every package. Wait for dispatched agents to finish. Preserve and resolve reported issues before treating a package as complete; report a blocker when the work cannot be completed.

Integrate the returned changes using the project's conventions. Resolve overlapping edits, inspect the combined diff against the Plan and acceptance criteria, and check that no assigned work was lost. Do not infer completion from an agent's launch or omit a failed package.

Return Changes identifying the integrated code and test changes and any checks already performed, alongside Task, Repository, project instructions, Plan, and PR context. The parent workflow will run the focused tests on the integrated result.
