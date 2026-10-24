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
BASIC = f'flowchart TD\n{START}\n{STOP}\nclick _start href "steps/_start.md"\nclick _stop href "steps/_stop.md"\n_start --> _stop'
DECISION = f'''flowchart TD
{START}
a["A"]
b["B"]
click a href "steps/a.md"
click b href "steps/b.md"
{STOP}
click _start href "steps/_start.md"
click _stop href "steps/_stop.md"
_start -->|a is supported| a
_start -->|b is supported| b
a --> _stop
b --> _stop'''
PARALLEL = f'''flowchart TD
{START}
split@{{ shape: fork, label: "fork" }}
a["A [subagent:fresh]"]
b["B [subagent:inherit]"]
click a href "steps/a.md"
click b href "steps/b.md"
click split href "steps/split.md"
click gather href "steps/gather.md"
gather@{{ shape: fork, label: "join" }}
{STOP}
click _start href "steps/_start.md"
click _stop href "steps/_stop.md"
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
            BASIC + '\norphan["Orphan"]\nclick orphan href "steps/a.md"\norphan --> _stop',
            BASIC + "\n_stop --> _start",
            BASIC + "\nclick _start call evil()",
            BASIC + "\n%%{init: {}}%%",
            DECISION.replace("a --> _stop", "a --> a"),
            DECISION.replace("-->|b is supported|", "-->"),
            DECISION.replace("b is supported", "a is supported"),
            PARALLEL.replace('label: "fork"', 'label: "Fork or Join"'),
            PARALLEL.replace("split --> a", "split -->|ready| a"),
            PARALLEL.replace("a --> gather", "a -->|ready| gather"),
            PARALLEL.replace("[subagent:fresh]", "[subagent:unknown]"),
            PARALLEL.replace("[subagent:fresh]", "[subagent:fresh] [subagent:inherit]"),
            PARALLEL.replace('a["A [subagent:fresh]"]', '%% subagent:fresh\na["A"]'),
            PARALLEL + "\n%% subagent:fresh",
            DECISION.replace('href "steps/a.md"', 'href "/a.md"'),
            DECISION.replace('href "steps/a.md"', 'href "https://example.com/a.md"'),
            DECISION.replace('click a href "steps/a.md"', ''),
            DECISION + '\nclick a href "steps/a.md"',
            DECISION + '\nclick absent href "steps/a.md"',
            DECISION.replace('a["A"]', 'a["editor:review"]'),
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
    def test_entry_returns_start_before_advancing(self) -> None:
        filename = self.write(DECISION)
        start = str(filename.parent / "steps/_start.md")
        self.assertEqual(wf.run(["start", str(filename)]), [start])
        result = subprocess.run([sys.executable, str(SCRIPT), "start", str(filename)], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, start + "\n", ""))
        self.assertEqual(wf.run(["next", str(filename), "start", "--true", "a", "--false", "b"]), [str(filename.parent / "steps/a.md")])
        result = subprocess.run([sys.executable, str(SCRIPT), "next", str(filename), "stop"], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        with self.assertRaises(ValueError):
            wf.run(["next", str(filename)])
        with self.assertRaises(ValueError):
            wf.run(["start", str(filename), "--true", "a"])
        with self.assertRaises(ValueError):
            wf.run(["start", str(filename), "start"])
        with self.assertRaises(ValueError):
            wf.run(["fork", str(filename)])

    def test_navigation_instructions_and_silent_validation(self) -> None:
        filename = self.write(PARALLEL)
        steps = filename.parent / "steps"
        self.assertEqual(wf.run(["validate", str(filename)]), [])
        self.assertEqual(wf.run(["next", str(filename), "_start"]), [str(steps / "split.md")])
        expected = [f"Spawn a subagent with fresh context: {steps / 'a.md'}", f"Spawn a subagent inheriting the context from this thread: {steps / 'b.md'}"]
        self.assertEqual(wf.run(["fork", str(filename), "split"]), expected)
        self.assertEqual(wf.run(["next", str(filename), "split"]), expected)
        result = subprocess.run([sys.executable, str(SCRIPT), "next", str(filename), "split"], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "\n".join(expected) + "\n", ""))
        self.assertEqual(wf.run(["next", str(filename), "_stop"]), [])
        with self.assertRaises(ValueError):
            wf.run(["fork", str(filename), "split", "--true", "a"])
        result = subprocess.run([sys.executable, str(SCRIPT), "validate", str(filename)], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_help_keeps_stdout_empty(self) -> None:
        result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertIn("usage:", result.stderr)

    def test_named_links_resolve_relative_to_the_graph(self) -> None:
        filename = self.write(DECISION)
        linked = filename.parent / "instructions/request.md"
        linked.parent.mkdir()
        (filename.parent / "steps/a.md").rename(linked)
        filename.write_text(filename.read_text().replace('href "steps/a.md"', 'href "instructions/request.md"'))
        renamed = filename.rename(filename.with_name("entry.md"))
        self.assertEqual(wf.run(["start", str(renamed)]), [str(renamed.parent / "steps/_start.md")])
        self.assertEqual(wf.run(["next", str(renamed), "start", "--true", "a", "--false", "b"]), [str(linked)])

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
        graph = DECISION.replace('a["A"]', 'a["example:review"]').replace('click a href "steps/a.md"\n', '')
        filename = self.write(graph)
        child = self.write(name="review")
        self.assertEqual(wf.run(["next", str(filename), "_start", "--true", "a", "--false", "b", "--root", str(self.root)]), ["example:review"])
        self.assertEqual(wf.run(["start", str(child)]), [str(child.parent / "steps/_start.md")])
        self.assertEqual(wf.run(["next", str(child), "_start"]), [str(child.parent / "steps/_stop.md")])
        self.assertEqual(wf.run(["next", str(child), "_stop"]), [])
        self.assertEqual(wf.run(["next", str(filename), "a"]), [str(filename.parent / "steps/_stop.md")])
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

    def test_annotated_skill_reference_keeps_identifier(self) -> None:
        for preference, instruction in (
            ("fresh", "Spawn a subagent with fresh context"),
            ("inherit", "Spawn a subagent inheriting the context from this thread"),
        ):
            with self.subTest(preference=preference):
                graph = DECISION.replace('a["A"]', f'a["example:review [subagent:{preference}]"]').replace('click a href "steps/a.md"\n', '')
                filename = self.write(graph)
                self.assertEqual(wf.load(filename).nodes["a"].target, "example:review")
                self.assertEqual(
                    wf.run(["next", str(filename), "_start", "--true", "a", "--false", "b"]),
                    [f"{instruction}: example:review"],
                )

    def test_missing_files_and_symlink_escape(self) -> None:
        filename = self.write(DECISION)
        target = filename.parent / "steps/a.md"
        target.unlink()
        outside = self.root / "outside.md"
        outside.write_text("Outside instructions.")
        target.symlink_to(outside)
        with self.assertRaises(ValueError):
            wf.load(filename)
        result = subprocess.run([sys.executable, str(SCRIPT), "next", str(filename), "_start"], capture_output=True, text=True)
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


class NestedWorkflowTests(Fixture):
    def nested(self, filename: Path, graph: str = BASIC) -> Path:
        """Create a reusable workflow without skill metadata or a SKILL.md entry."""
        graph = graph.replace('"steps/', f'"{filename.stem}/')
        filename.write_text("---\nmetadata:\n  workflow: mermaid-v1\n---\n\n```mermaid\n" + graph + "\n```\n")
        directory = filename.with_suffix("")
        directory.mkdir(exist_ok=True)
        (directory / "_start.md").write_text("## Inputs\n- Text.\nReturn Text unchanged.\n")
        (directory / "_stop.md").write_text("## Outputs\n- Text, unchanged.\n")
        return filename

    def test_markdown_workflow_entry_and_return(self) -> None:
        parent = self.write(DECISION.replace('href "steps/a.md"', 'href "steps/implement.md"'))
        child = self.nested(parent.parent / "steps/implement.md")
        self.assertEqual(wf.run(["next", str(parent), "_start", "--true", "a", "--false", "b"]), [str(child)])
        self.assertEqual(wf.run(["start", str(child)]), [str(child.with_suffix("") / "_start.md")])
        self.assertEqual(wf.run(["next", str(child), "_start"]), [str(child.with_suffix("") / "_stop.md")])
        self.assertEqual(wf.run(["next", str(child), "_stop"]), [])
        self.assertEqual(wf.run(["next", str(parent), "a"]), [str(parent.parent / "steps/_stop.md")])

    def test_deeper_nesting_and_broken_child_references(self) -> None:
        graph = BASIC.replace("_start --> _stop", 'child["Child"]\nclick child href "steps/child.md"\n_start --> child\nchild --> _stop')
        parent = self.write(graph)
        child = self.nested(parent.parent / "steps/child.md", graph)
        grandchild = self.nested(child.with_suffix("") / "child.md")
        wf.load(parent)
        self.assertEqual(wf.run(["start", str(grandchild)]), [str(grandchild.with_suffix("") / "_start.md")])
        grandchild.write_text(grandchild.read_text().replace("flowchart TD", "flowchart LR"))
        with self.assertRaises(ValueError):
            wf.load(parent)
        self.nested(grandchild)
        (grandchild.with_suffix("") / "_stop.md").unlink()
        with self.assertRaises(FileNotFoundError):
            wf.load(parent)

    def test_nested_recursive_reference_and_symlink_escape(self) -> None:
        graph = BASIC.replace("_start --> _stop", 'child["Child"]\nclick child href "steps/child.md"\n_start --> child\nchild --> _stop')
        parent = self.write(graph)
        child = self.nested(parent.parent / "steps/child.md", graph)
        link = child.with_suffix("") / "child.md"
        link.symlink_to(child)
        wf.load(parent)
        link.unlink()
        outside = self.root / "outside.md"
        outside.write_text("Unrelated instructions.")
        link.symlink_to(outside)
        with self.assertRaises(ValueError):
            wf.load(parent)


class LayoutTests(unittest.TestCase):
    def test_one_discoverable_skill_with_bundled_instructions(self) -> None:
        directory = ROOT / "skills/graph-workflows"
        self.assertEqual(list((ROOT / "skills").rglob("SKILL.md")), [directory / "SKILL.md"])
        for resource in ("standard", "writing", "executing"):
            self.assertTrue((directory / "references" / f"{resource}.md").is_file())
        self.assertTrue((directory / "scripts/workflow.py").is_file())


class AuthoringExampleTests(unittest.TestCase):
    def test_review_and_revision_before_delivery(self) -> None:
        filename = ROOT / "skills/graph-workflows/references/examples/write-workflow/WORKFLOW.md"
        workflow = wf.load(filename)
        self.assertEqual(wf.run(["start", str(filename)]), [str(filename.parent / "steps/_start.md")])
        routes = [
            ["_start", "design", "write", "review", "check", "_stop"],
            ["_start", "design", "write", "review", "check", "write", "review", "check", "_stop"],
        ]
        for route in routes:
            with self.subTest(route=route):
                for source, target in zip(route, route[1:]):
                    arguments = ["next", str(filename), source]
                    for edge in workflow.edges:
                        if edge.source == source and edge.condition:
                            arguments.extend(["--true" if edge.target == target else "--false", edge.target])
                    expected = str(wf.instruction(workflow, workflow.nodes[target]))
                    if target == "review":
                        expected = f"Spawn a subagent with fresh context: {expected}"
                    self.assertEqual(wf.run(arguments), [expected])
                self.assertEqual(wf.run(["next", str(filename), "stop"]), [])


class CodingExampleTests(unittest.TestCase):
    def test_nested_implementation_returns_before_focused_tests(self) -> None:
        parent = ROOT / "skills/graph-workflows/references/examples/write-code/WORKFLOW.md"
        child = parent.parent / "steps/implement.md"
        self.assertEqual(wf.run(["next", str(parent), "plan"]), [str(child)])
        self.assertEqual(wf.run(["start", str(child)]), [str(child.with_suffix("") / "_start.md")])
        route = ["_start", "partition", "dispatch", "collect", "_stop"]
        workflow = wf.load(child)
        for source, target in zip(route, route[1:]):
            self.assertEqual(wf.run(["next", str(child), source]), [str(wf.instruction(workflow, workflow.nodes[target]))])
        self.assertEqual(wf.run(["next", str(child), "_stop"]), [])
        self.assertEqual(wf.run(["next", str(parent), "implement"]), [str(parent.parent / "steps/tests.md")])

    def test_success_and_repair_routes_end_at_pr_link(self) -> None:
        filename = ROOT / "skills/graph-workflows/references/examples/write-code/WORKFLOW.md"
        workflow = wf.load(filename)
        routes = [
            ["_start", "plan", "implement", "tests", "pr", "_stop"],
            ["_start", "plan", "implement", "tests", "implement", "tests", "pr", "_stop"],
            ["_start", "plan", "implement", "tests", "repair_tests", "tests", "pr", "_stop"],
        ]
        for route in routes:
            with self.subTest(route=route):
                for source, target in zip(route, route[1:]):
                    decisions: dict[str, wf.Decision] = {
                        edge.target: "true" if edge.target == target else "false"
                        for edge in workflow.edges if edge.source == source and edge.condition
                    }
                    self.assertEqual([node.name for node in wf.select(workflow, source, decisions)], [target])
                    arguments = ["next", str(filename), source]
                    for name, decision in decisions.items():
                        arguments.extend([f"--{decision}", name])
                    expected = str(wf.instruction(workflow, workflow.nodes[target]))
                    self.assertEqual(wf.run(arguments), [expected])
                self.assertEqual(wf.run(["next", str(filename), "_stop"]), [])


if __name__ == "__main__":
    unittest.main()
