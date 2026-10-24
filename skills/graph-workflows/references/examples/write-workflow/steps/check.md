# Validate and traverse the candidate

Given Requirements, Skill identity, Destination, project instructions, Standard, Design, Candidate, and Review findings, run the graph-workflows CLI to validate the generated skill and locally available references. Record commands and results as Validation evidence.

Use start to verify entry, then navigate representative success and failure cases from Design. Exercise declared decision assessments, nested entry and return, any fork branches, and stop. Inspect each returned instruction path or skill reference. Keep these checks focused and follow the project's testing rules.

Combine review findings and validation failures as Findings. Return Outcome `revise` when corrections remain, or `ready` when the checks pass and no findings remain. Return Findings, Validation evidence, and all supplied artifacts for revision or completion. Report unresolved requirements or unavailable checks as blockers rather than claiming readiness.
