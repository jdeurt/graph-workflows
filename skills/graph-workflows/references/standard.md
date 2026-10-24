# Graph workflow standard

A graph workflow is a skill with this frontmatter marker:

```yaml
metadata:
  workflow: mermaid-v1
```

Keep the standard name and description fields. Put one Mermaid fence first in the body, followed only by optional `## Notes` bullets. Use `flowchart TD`.

## Nodes and Markdown

| Node | Declaration | Instructions |
| --- | --- | --- |
| Start | `_start@{ shape: sm-circ, label: "Start" }` | `steps/_start.md` |
| Stop | `_stop@{ shape: framed-circle, label: "Stop" }` | `steps/_stop.md` |
| Markdown instructions | `draft["draft.md"]` | `steps/draft.md` |
| Skill reference | `review["editor:review"]` | The referenced skill |
| Fork | `split@{ shape: fork, label: "fork" }` | `steps/split.md` |
| Join | `gather@{ shape: fork, label: "join" }` | `steps/gather.md` |

Declare each node once. Identifiers contain letters, digits, and underscores and start with a letter or underscore. A normal node names either a Markdown filename within steps or a plugin:skill identifier. The referenced skill can be prose or a graph workflow.

Each Markdown file must explain its purpose, required inputs, actions, and returned outputs without another node's prose or hidden history. Pass previous results as explicit artifacts. Headings are optional except where this standard locates a contract or pairing.

Start's Inputs bullets define the workflow inputs. Stop's Outputs bullets define its returned results. Stop can name a Markdown template under Output template, relative to its own file. Templates are text, never executable code. Nodes choose their own work locations; this standard prescribes no output or scratch directories.

## Edges

Use `a --> b` for unconditional flow and `a -->|condition| b` for a decision. Never mix unconditional and conditional edges from one source. Edges out of a fork and into a join must be unconditional.

A decision takes exactly one true condition after assessing every outgoing condition. Unknown evidence, multiple true conditions, or no true condition blocks execution. Edge order gives no priority. Conditions require agent judgment; validation cannot prove their truth or completeness.

Use one declaration or edge per line. The CLI accepts this subset, blank lines, and Mermaid comments. It does not execute Mermaid, HTML, directives, or handlers. Every node must be reachable from start and have a route to stop. Start has no incoming edges; stop has no outgoing edges. Cycles and recursive references have no imposed execution cap.

## Threads and skill references

Place `%% subagent:fresh` or `%% subagent:inherit` before the next node declaration. Blank lines do not change the association. No annotation means continue on the same thread. Fresh requests only declared inputs and necessary instructions; inherit requests available context.

These are preferences. Use the closest supported behavior when the harness lacks subagents, context control, or parallelism. Still execute the work, without routine capability disclaimers or false capability claims.

Supply a referenced skill's inputs explicitly. Run a referenced workflow from start through stop, then return its declared results to the parent before selecting another edge. Follow a prose skill's own instructions. Resolve missing or ambiguous inputs before acting. Missing skills block execution; the CLI can only check locally available references.

## Fork and join

Fork dispatches every outgoing branch. A fork's Markdown instructions include a Join section naming its matching join:

```markdown
## Join

gather
```

This pairing identifies where nested branches return. Branch inputs and returned outputs stay free-form. Join's Markdown instructions describe how to combine those outputs; its graph label already identifies the role, so no duplicate role field is needed.

Run branches concurrently when supported, following their thread annotations. Otherwise execute them using the closest supported arrangement. Keep each branch's artifacts explicit and coordinate shared effects. Wait for every branch before executing the join once. Propagate failures unless its instructions define authorized recovery. Never substitute missing results with success.

Branches must stay separate until their matching join. Nested forks and multiple nodes per branch are allowed. A graph route to stop does not prove runtime termination. Continue only while the conditions and authorized task justify the work.

## CLI

Run `python3 /path/to/graph-workflows/scripts/workflow.py` with one of:

- `validate FILE`: check local graph and references; success produces no stdout.
- `show FILE NODE`: return that node's instruction path or skill identifier.
- `next FILE NODE`: return the next path or identifier. Supply `--true TARGET` or `--false TARGET` for each conditional target. Resolve uncertainty before calling next.
- `fork FILE NODE`: return every branch target, one per line. No condition flags apply.

There is no JSON envelope or status chatter. Stop has no next target. Errors go to stderr with a nonzero exit status. The CLI does not execute instructions, judge conditions, or create agents.

Use `--root DIR` to check local plugin or skill collections. Instruction and template paths must remain inside their skill; physical link targets must remain inside the supplied root. Unavailable plugin namespaces remain skill identifiers for the harness to resolve.

Expanded shapes come from [Mermaid 11.3.0 and later](https://mermaid.js.org/syntax/flowchart.html#expanded-node-shapes-in-mermaid-flowcharts-v1130). The filename, pairing, and execution conventions above belong to this skill.
