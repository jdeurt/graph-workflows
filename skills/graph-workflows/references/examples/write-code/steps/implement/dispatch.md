# Delegate the work packages

Given Assignments containing N and N self-contained work packages, Task, Repository, project instructions, Plan, PR context, and any Failure evidence, dispatch one agent per package. Run the N packages concurrently where supported. Prefer fresh contexts, supplying each agent its package, relevant task and code evidence, project instructions, and access needed for the assigned changes.

Tell each agent to implement its package, update tests needed to verify its acceptance criteria without weakening them, and return changed code and tests, checks performed, and any unresolved issues. Keep edits within the agreed ownership and coordinate shared effects.

Retain a handle or result for every package. If the harness cannot provide N concurrent agents or fresh contexts, use the closest supported arrangement, including sequential execution. Complete every package; do not claim delegation or isolation that did not occur.

Return Work containing every package's handle or completed result, alongside Assignments, Task, Repository, project instructions, Plan, PR context, and Failure evidence. Leave collection and integration to the next instructions.
