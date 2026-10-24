# Write or edit a workflow

Read the standard and any existing workflow before editing. Establish the task, inputs, outputs, and evidence of completion. Keep the graph and its Markdown instructions consistent.

1. Preserve standard skill frontmatter and the workflow marker.
2. Put the top-down Mermaid graph first, with optional Notes bullets afterward.
3. Define start inputs and stop outputs as free-form bullets.
4. Give each normal node a Markdown filename or skill identifier.
5. Write self-contained instructions with explicit inputs and outputs.
6. Use conditions for decisions and unlabeled edges for unconditional flow.
7. Use fork and join labels for concurrency, with no conditions out of fork or into join.
8. Name each fork's matching join in its Markdown instructions.
9. Add a subagent comment only when a different thread is useful.

Use an output template only when it helps produce the required result. Keep Notes execution-relevant. Do not add work-directory conventions, execution limits, or unrelated features.

Validate the graph and references. Exercise a representative task, relevant failures, nested returns, and parallel completion. Review node instructions using only their declared inputs. Static checks cannot establish semantic self-containment or condition truth.

Have an independent reader review material changes when available. Resolve findings and report the actual checks and remaining limits. Keep examples as supporting references, not additional installed skills.

Use the [release-brief example](example.md) to see nested skill references and parallel review together.

Use the [coding example](examples/write-code/WORKFLOW.md) for planning, implementation, focused-test repair loops, and PR creation. It ends with the PR link without waiting for CI. Its WORKFLOW.md filename keeps it a supporting example rather than an installed skill.
