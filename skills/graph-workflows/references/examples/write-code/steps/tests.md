# Run focused tests

Given Task, Repository, project instructions, Plan, Changes, and PR context, run the focused test commands from Plan against the current changes. Preserve the commands, results, and relevant failure details as Test evidence.

If tests fail, compare the failures with the acceptance criteria and relevant code. Classify the next repair as incorrect implementation or incorrect tests. If both need repair, choose implementation first and include both findings. Resolve uncertain causes before selecting a repair; report a blocker if evidence or access is insufficient. An unavailable test environment is not a passing result.

Return one Outcome: `pass`, `repair implementation`, or `repair tests`. Return Test evidence and any Failure evidence, alongside Task, Repository, project instructions, Plan, Changes, and PR context.
