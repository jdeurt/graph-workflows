# Partition the implementation

Given Task, Repository, project instructions, Plan, PR context, and any Failure evidence, inspect the affected code. Divide the implementation and necessary tests into independently actionable work packages. Choose N from the useful independent work and the harness's available agent capacity. Use one package when the change cannot usefully be divided or delegation is unavailable.

For each package, state its purpose, acceptance criteria, owned code or tests, required inputs, instructions, dependencies, and returned change evidence. Separate overlapping edits or keep dependent changes in one package. Together the packages must cover the Plan and any repairs identified by Failure evidence.

Return Assignments containing N and the N work packages, alongside Task, Repository, project instructions, Plan, PR context, and Failure evidence.
