# Graph workflows

One skill for reading, creating, editing, and executing Markdown workflows with Mermaid graphs. Start with [SKILL.md](skills/graph-workflows/SKILL.md).

The typed Python CLI uses only the standard library and requires Python 3.10 or later:

```sh
python3 skills/graph-workflows/scripts/workflow.py validate /path/to/SKILL.md
python3 skills/graph-workflows/scripts/workflow.py show /path/to/SKILL.md node
python3 skills/graph-workflows/scripts/workflow.py next /path/to/SKILL.md decision --true accepted --false revise
```

Navigation prints only instruction paths or skill identifiers. Successful validation is silent. Agents execute the instructions; the CLI does not.

## Claude Code and Codex

Build native single-skill bundles with [Soubi](https://soubi.vercel.app/docs):

```sh
python3 scripts/package.py
```

Packaging requires Node.js 20 or later and npx. Bundles appear in `.soubi-out/claude` and `.soubi-out/codex`. The build stages only skill files, so repository contributor instructions stay out of the bundles. There is no marketplace.

## Development

Run focused tests while editing, for example `python3 -m unittest tests.test_workflow.GraphTests`. CI runs the full suite, strict mypy checks, and both Soubi builds. Mypy and Soubi are development tools, not CLI dependencies.
