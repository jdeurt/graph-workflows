"""Focused parser, reference, navigation, and skill-layout checks."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/graph-workflows/scripts/workflow.py"
sys.path.insert(0, str(SCRIPT.parent))
import workflow as wf

START = '_start@{ shape: sm-circ, label: "Start" }'
STOP = '_stop@{ shape: framed-circle, label: "Stop" }'
BASIC = f"flowchart TD\n{START}\n{STOP}\n_start --> _stop"
DECISION = f'''flowchart TD
{START}
a["a.md"]
b["b.md"]
{STOP}
_start -->|a is supported| a
_start -->|b is supported| b
a --> _stop
b --> _stop'''
PARALLEL = f'''flowchart TD
{START}
split@{{ shape: fork, label: "fork" }}
%% subagent:fresh
a["a.md"]
%% subagent:inherit
b["b.md"]
gather@{{ shape: fork, label: "join" }}
{STOP}
_start --> split
split --> a
split --> b
a --> gather
b --> gather
gather --> _stop'''


def entry(graph: str) -> str:
    """Write the documented marker and graph-first entry layout."""
    return f"---\nname: sample\ndescription: Return supplied text.\nmetadata:\n  workflow: mermaid-v1\n---\n\n```mermaid\n{graph}\n```\n"


class Fixture(unittest.TestCase):
    """Own a temporary plugin registry for each test."""

    def setUp(self) -> None:
        self.temporary: TemporaryDirectory[str] = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, graph: str = BASIC, name: str = "sample") -> Path:
        """Create a workflow with explicit synthetic instructions and contracts."""
        directory = self.root / "example/skills" / name
        steps = directory / "steps"
        steps.mkdir(parents=True, exist_ok=True)
        filename = directory / "SKILL.md"
        filename.write_text(entry(graph), encoding="utf-8")
        (steps / "_start.md").write_text("## Inputs\n- Text: supplied text.\nRetain Text unchanged.\n", encoding="utf-8")
        (steps / "_stop.md").write_text("## Outputs\n- Text: supplied text, unchanged.\n", encoding="utf-8")
        for target in ("a", "b", "x", "y"):
            (steps / f"{target}.md").write_text("Given Text, return Text unchanged.\n", encoding="utf-8")
        (steps / "split.md").write_text("## Join\n\ngather\n", encoding="utf-8")
        (steps / "gather.md").write_text("Combine the declared branch outputs.\n", encoding="utf-8")
        return filename


class GraphTests(Fixture):
    def test_marker_and_graph_first_layout(self) -> None:
        filename = self.write()
        self.assertTrue(wf.marked(filename.read_text()))
        self.assertFalse(wf.marked("---\nname: ordinary\n---\nProse."))
        self.assertEqual(set(wf.parse(filename).nodes), {"_start", "_stop"})
        filename.write_text(entry(BASIC) + "\n## Notes\n\n- Supplied context.\n")
        wf.parse(filename)
        filename.write_text(entry(BASIC).replace("```mermaid", "Introduction\n```mermaid"))
        with self.assertRaises(ValueError):
            wf.parse(filename)

    def test_invalid_graphs(self) -> None:
        cases = [
            BASIC.replace("flowchart TD", "flowchart LR"),
            BASIC.replace(STOP, ""),
            BASIC + f"\n{START}",
            BASIC.replace("_start --> _stop", "_start --> absent"),
            BASIC + '\norphan["a.md"]\norphan --> _stop',
            BASIC + "\n_stop --> _start",
            BASIC + "\nclick _start call evil()",
            BASIC + "\n%%{init: {}}%%",
            DECISION.replace("a --> _stop", "a --> a"),
            DECISION.replace("-->|b is supported|", "-->"),
            DECISION.replace("b is supported", "a is supported"),
            PARALLEL.replace('label: "fork"', 'label: "Fork or Join"'),
            PARALLEL.replace("split --> a", "split -->|ready| a"),
            PARALLEL.replace("a --> gather", "a -->|ready| gather"),
            PARALLEL.replace("%% subagent:fresh", "%% subagent:unknown"),
            PARALLEL + "\n%% subagent:fresh",
            DECISION.replace("a.md", "../a.md"),
        ]
        for graph in cases:
            with self.subTest(graph=graph), self.assertRaises(ValueError):
                wf.parse(self.write(graph))

    def test_direct_marker_in_block_and_flow_metadata(self) -> None:
        for metadata in ("metadata:\n  workflow: mermaid-v1", "metadata: {workflow: mermaid-v1}", 'metadata: {author: "a,b", workflow: "mermaid-v1"}'):
            self.assertTrue(wf.marked(f"---\n{metadata}\n---\n"))
        for metadata in ("metadata:\n  nested:\n    workflow: mermaid-v1", "metadata: |\n  workflow: mermaid-v1", 'metadata: {note: "x, workflow: mermaid-v1"}'):
            self.assertFalse(wf.marked(f"---\n{metadata}\n---\n"))

    def test_context_and_unconditional_concurrency(self) -> None:
        workflow = wf.load(self.write(PARALLEL))
        self.assertEqual(workflow.nodes["a"].agent, "fresh")
        self.assertEqual(workflow.nodes["b"].agent, "inherit")
        self.assertIsNone(workflow.nodes["gather"].agent)
        self.assertEqual(workflow.joins, {"split": "gather"})
        self.assertEqual([node.name for node in wf.select(workflow, "split", {})], ["a", "b"])

    def test_branch_pairing(self) -> None:
        for graph in [PARALLEL.replace("a --> gather", "a --> _stop"), PARALLEL.replace("a --> gather", "a --> b")]:
            with self.subTest(graph=graph), self.assertRaises(ValueError):
                wf.load(self.write(graph))
        filename = self.write(PARALLEL)
        (filename.parent / "steps/split.md").write_text("## Join\n\nmissing\n")
        with self.assertRaises(ValueError):
            wf.load(filename)

    def test_cycles_with_an_exit(self) -> None:
        graph = DECISION.replace("a --> _stop", "a -->|retry is justified| a\na -->|result is complete| _stop")
        workflow = wf.load(self.write(graph))
        self.assertEqual(wf.select(workflow, "a", {"a": "false", "_stop": "true"})[0].name, "_stop")


class NavigationTests(Fixture):
    def test_plain_targets_and_silent_validation(self) -> None:
        filename = self.write(PARALLEL)
        steps = filename.parent / "steps"
        self.assertEqual(wf.run(["validate", str(filename)]), [])
        self.assertEqual(wf.run(["show", str(filename), "a"]), [str(steps / "a.md")])
        self.assertEqual(wf.run(["fork", str(filename), "split"]), [str(steps / "a.md"), str(steps / "b.md")])
        self.assertEqual(wf.run(["next", str(filename), "_stop"]), [])
        with self.assertRaises(ValueError):
            wf.run(["fork", str(filename), "split", "--true", "a"])
        result = subprocess.run([sys.executable, str(SCRIPT), "validate", str(filename)], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_help_keeps_stdout_empty(self) -> None:
        result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertIn("usage:", result.stderr)

    def test_decisions_need_complete_unique_evidence(self) -> None:
        workflow = wf.load(self.write(DECISION))
        self.assertEqual(wf.select(workflow, "_start", {"a": "true", "b": "false"})[0].name, "a")
        cases: list[dict[str, wf.Decision]] = [{}, {"a": "true"}, {"a": "true", "b": "true"}, {"a": "false", "b": "false"}]
        for decisions in cases:
            with self.subTest(decisions=decisions), self.assertRaises(ValueError):
                wf.select(workflow, "_start", decisions)
        filename = self.write(DECISION)
        with self.assertRaises(ValueError):
            wf.run(["next", str(filename), "_start", "--true", "a", "--false", "a"])

    def test_skill_reference_is_an_identifier(self) -> None:
        graph = DECISION.replace('a["a.md"]', 'a["example:review"]')
        filename = self.write(graph)
        child = self.write(name="review")
        self.assertEqual(wf.run(["show", str(filename), "a", "--root", str(self.root)]), ["example:review"])
        child.write_text(entry(BASIC.replace("flowchart TD", "flowchart LR")).replace("metadata:\n  workflow: mermaid-v1", "metadata: {workflow: mermaid-v1}"))
        with self.assertRaises(ValueError):
            wf.load(filename, self.root)
        child.write_text("---\nname: review\ndescription: Review text.\n---\n## Example\nOne.\n## Example\nTwo.\n")
        wf.load(filename, self.root)
        child.write_text(entry(graph.replace("example:review", "example:sample")))
        wf.load(filename, self.root)
        child.unlink()
        with self.assertRaises(FileNotFoundError):
            wf.load(filename, self.root)

    def test_missing_files_and_symlink_escape(self) -> None:
        filename = self.write(DECISION)
        target = filename.parent / "steps/a.md"
        target.unlink()
        outside = self.root / "outside.md"
        outside.write_text("Outside instructions.")
        target.symlink_to(outside)
        with self.assertRaises(ValueError):
            wf.load(filename)
        result = subprocess.run([sys.executable, str(SCRIPT), "show", str(filename), "a"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("bundle root", result.stderr)

    def test_contracts_and_template(self) -> None:
        filename = self.write()
        stop = filename.parent / "steps/_stop.md"
        stop.write_text("## Outputs\n- Text.\n## Output template\n../result.md\n")
        with self.assertRaises(FileNotFoundError):
            wf.load(filename)
        (filename.parent / "result.md").write_text("{{Text}}\n")
        wf.load(filename)
        stop.write_text("Missing output contract.")
        with self.assertRaises(ValueError):
            wf.load(filename)


class LayoutTests(unittest.TestCase):
    def test_one_discoverable_skill_with_bundled_instructions(self) -> None:
        directory = ROOT / "skills/graph-workflows"
        self.assertEqual(list((ROOT / "skills").rglob("SKILL.md")), [directory / "SKILL.md"])
        for resource in ("standard", "writing", "executing", "example"):
            self.assertTrue((directory / "references" / f"{resource}.md").is_file())
        self.assertTrue((directory / "scripts/workflow.py").is_file())


if __name__ == "__main__":
    unittest.main()
