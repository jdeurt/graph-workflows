# Working on this repository

This repository contains one skill: graph-workflows.

Keep documentation concise. Each instruction must help someone write or execute a workflow. Keep the shared standard, guidance, examples, and CLI consistent.

Use typed Python and the standard library for the CLI. Keep stdout limited to instruction paths or skill identifiers. Send errors to stderr. Agents execute workflows; the CLI only validates and navigates.

Run focused unittest cases while editing. Check Python types. Leave the complete test suite to CI.

Keep the skill installable with npx skills. Do not add plugin packaging, a marketplace, or generated output.

Push reviewed increments to main.
