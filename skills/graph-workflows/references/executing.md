# Read and execute a workflow

For reading-only requests, inspect or explain the requested content without executing its actions.

Read the standard, graph, Notes, start inputs, and stop outputs. Resolve the required inputs and skills before acting. Validate local files with the CLI when available; otherwise inspect them directly.

Do the work the workflow prescribes. Do not narrate workflow execution, node changes, navigation commands, branch dispatch, or control flow. Avoid statements such as “I'm executing this workflow” or “I'll run this node next.” Commands used to navigate or validate the workflow need no commentary unless the user requests a walkthrough.

Communicate task results, necessary questions, and actual blockers when the task calls for them. If the user asks whether or how a graph workflow is being used, answer truthfully. Silence about routine mechanics is not permission to conceal or misrepresent them.

Begin with `start FILE`, which returns its start instruction path without following an edge. Execute those instructions, then use `next FILE start` to advance. Read each Markdown instruction file or referenced skill and supply its inputs explicitly. Retain its declared outputs. Honor user scope, permissions, and project rules; the workflow grants no new authority.

When navigation returns a spawn instruction, use its requested context and target with the closest supported harness behavior. The instruction is a preference, not evidence that an agent has been created.

At decisions, assess all conditions and select exactly one true edge. At forks, execute every branch using its thread preference and the closest supported harness behavior. Keep branch artifacts separate. Continue at the matching join only after all branch outcomes are available.

Check Markdown targets as well as referenced skills for the workflow marker. For a graph workflow, read its graph, Notes, and stop contract, then call `start CHILD_FILE` to enter at its start instructions. Resolve its Markdown paths in the instruction directory defined by the standard. Run through its stop before returning the declared outputs to the caller. An unannotated successor continues on the same thread. Do not infer inputs from another node's hidden reasoning, even with inherited context.

When next returns the stop instruction path, execute it and return its Outputs using any named template. Calling next on stop returns nothing with a successful exit; do not seek another node. A nested workflow resumes its caller; a top-level workflow finishes. On failure, preserve completed effects and identify the information or action needed to recover. Check uncertain external outcomes before retrying. Resume only while the retained artifacts remain valid.
