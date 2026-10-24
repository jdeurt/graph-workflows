# Read and execute a workflow

For reading-only requests, inspect or explain the requested content without executing its actions.

Read the standard, graph, Notes, start inputs, and stop outputs. Resolve the required inputs and skills before acting. Validate local files with the CLI when available; otherwise inspect them directly.

Do the work the workflow prescribes. Do not narrate workflow execution, node changes, navigation commands, branch dispatch, or control flow. Avoid statements such as “I'm executing this workflow” or “I'll run this node next.” Commands used to navigate or validate the workflow need no commentary unless the user requests a walkthrough.

Communicate task results, necessary questions, and actual blockers when the task calls for them. If the user asks whether or how a graph workflow is being used, answer truthfully. Silence about routine mechanics is not permission to conceal or misrepresent them.

Begin at start. Read each Markdown instruction file or referenced skill and supply its inputs explicitly. Retain its declared outputs. Honor user scope, permissions, and project rules; the workflow grants no new authority.

At decisions, assess all conditions and select exactly one true edge. At forks, execute every branch using its thread preference and the closest supported harness behavior. Keep branch artifacts separate. Continue at the matching join only after all branch outcomes are available.

A referenced workflow runs through its stop before returning. An unannotated successor continues on the same thread. Do not infer inputs from another node's hidden reasoning, even with inherited context.

Execute stop's instructions and return its outputs using any named template. On failure, preserve completed effects and identify the information or action needed to recover. Check uncertain external outcomes before retrying. Resume only while the retained artifacts remain valid.
