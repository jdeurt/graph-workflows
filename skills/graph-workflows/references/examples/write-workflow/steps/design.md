# Design the workflow

Given Requirements, Skill identity, Destination, project instructions, and Standard, identify the actions, explicit inputs and outputs, conditions, and completion path. Use fork and join for graph branches that run concurrently. Include nested workflows or agent preferences where the task benefits from them.

Choose mutually exclusive decision outcomes and describe how uncertain evidence or failures will be resolved. Assign a self-contained instruction file to each Markdown-backed node, using paths relative to the workflow's instruction directory.

Return Design containing the graph, file locations, node contracts, and representative success and failure cases, alongside the supplied inputs.
