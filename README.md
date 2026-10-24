# Graph workflows

One skill for reading, creating, editing, and executing Markdown workflows with Mermaid graphs.

## Install

Use Node.js 22.20 or later:

```sh
npx skills add jdeurt/graph-workflows
```

Choose Claude Code, Codex, or another supported agent. The repository contains one skill: [graph-workflows](skills/graph-workflows/SKILL.md).

## CLI

The bundled CLI requires Python 3.10 or later and uses only the standard library. Replace `/path/to/graph-workflows` with the installed skill directory:

```sh
python3 /path/to/graph-workflows/scripts/workflow.py validate /path/to/SKILL.md
python3 /path/to/graph-workflows/scripts/workflow.py start /path/to/SKILL.md
python3 /path/to/graph-workflows/scripts/workflow.py next /path/to/SKILL.md start
python3 /path/to/graph-workflows/scripts/workflow.py next /path/to/SKILL.md decision --true accepted --false revise
```

`start FILE` returns the workflow's start instruction path. After executing those instructions, `next FILE start` follows its outgoing edge. Navigation returns an instruction path or skill identifier, prefixed with a spawn instruction for nodes marked `[subagent:fresh]` or `[subagent:inherit]`. Successful validation is silent. Agents execute the instructions; the CLI does not.

## Examples

The [coding workflow](skills/graph-workflows/references/examples/write-code/WORKFLOW.md) plans a change, delegates implementation through a [nested workflow](skills/graph-workflows/references/examples/write-code/steps/implement.md), repairs focused-test failures, and opens a PR. It returns the PR link without waiting for CI.

The [workflow-authoring example](skills/graph-workflows/references/examples/write-workflow/WORKFLOW.md) designs a graph workflow skill, writes its files, reviews it in fresh context, and validates it through a revision loop.

## Example transcript

Illustrative run of the coding workflow. The agent stays in `/workflows/write-code`, which contains WORKFLOW.md; the code repository is `/repo/cleanup`. File contents and implementation details are abbreviated.

**User:** Add a dry-run option to cleanup, test it, and open a PR.

**Shell:**

```sh
cli=/path/to/graph-workflows/scripts/workflow.py
cat WORKFLOW.md
python3 "$cli" start WORKFLOW.md
# /workflows/write-code/steps/_start.md
cat steps/_start.md
python3 "$cli" next WORKFLOW.md start
# /workflows/write-code/steps/plan.md
cat steps/plan.md
rg -n 'unlink|dry_run' /repo/cleanup/src /repo/cleanup/tests
```

**Agent:** The change needs a dry-run branch that reports files without deleting them, plus focused tests for both modes.

**Shell:**

```sh
python3 "$cli" next WORKFLOW.md plan
# /workflows/write-code/steps/implement.md
cat steps/implement.md
python3 "$cli" start steps/implement.md
# /workflows/write-code/steps/implement/_start.md
cat steps/implement/_start.md
python3 "$cli" next steps/implement.md start
# /workflows/write-code/steps/implement/partition.md
cat steps/implement/partition.md
```

**Agent:** Two independent packages: update `src/cleanup.py` and add focused cases in `tests/test_cleanup.py`.

**Shell:**

```sh
python3 "$cli" next steps/implement.md partition
# /workflows/write-code/steps/implement/dispatch.md
cat steps/implement/dispatch.md
```

**Agent tool:** Spawn two fresh-context agents. Give each its work package, acceptance criteria, relevant code, project rules, and required change evidence. Retain both handles.

**Shell:**

```sh
python3 "$cli" next steps/implement.md dispatch
# /workflows/write-code/steps/implement/collect.md
cat steps/implement/collect.md
```

**Agent tool:** Wait for both agents. Receive the implementation and test changes; integrate and inspect the combined diff.

**Shell:**

```sh
git -C /repo/cleanup diff --check
python3 "$cli" next steps/implement.md collect
# /workflows/write-code/steps/implement/_stop.md
cat steps/implement/_stop.md
python3 "$cli" next steps/implement.md stop
# No output; return the integrated Changes to the caller.
python3 "$cli" next WORKFLOW.md implement
# /workflows/write-code/steps/tests.md
cat steps/tests.md
(cd /repo/cleanup && python3 -m pytest -q tests/test_cleanup.py)
# 4 passed
python3 "$cli" next WORKFLOW.md tests --true pr --false implement --false repair_tests
# /workflows/write-code/steps/pr.md
cat steps/pr.md
git -C /repo/cleanup switch -c feature/dry-run
git -C /repo/cleanup add src/cleanup.py tests/test_cleanup.py
git -C /repo/cleanup commit -m "Add cleanup dry-run mode"
git -C /repo/cleanup push -u origin feature/dry-run
gh pr create --repo acme/cleanup --base main --head feature/dry-run --title "Add dry-run mode" --body "Adds dry-run mode. Focused tests: 4 passed."
# https://github.com/acme/cleanup/pull/42
python3 "$cli" next WORKFLOW.md pr
# /workflows/write-code/steps/_stop.md
cat steps/_stop.md
python3 "$cli" next WORKFLOW.md stop
# No output.
```

**Agent:** [PR](https://github.com/acme/cleanup/pull/42)

## Development

Run focused tests while editing, for example `python3 -m unittest tests.test_workflow.GraphTests`. CI runs the full suite, strict mypy checks, and installer checks. Mypy is a development tool, not a CLI dependency.
