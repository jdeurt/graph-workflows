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
python3 /path/to/graph-workflows/scripts/workflow.py next /path/to/SKILL.md decision --true accepted --false revise
```

Navigation prints only instruction paths or skill identifiers. Successful validation is silent. Agents execute the instructions; the CLI does not.

## Example

The [coding workflow](skills/graph-workflows/references/examples/write-code/WORKFLOW.md) plans a change, implements it, repairs focused-test failures, and opens a PR. It returns the PR link without waiting for CI.

## Development

Run focused tests while editing, for example `python3 -m unittest tests.test_workflow.GraphTests`. CI runs the full suite, strict mypy checks, and installer checks. Mypy is a development tool, not a CLI dependency.
