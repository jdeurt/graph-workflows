"""Validate and navigate graph workflows using only the Python standard library."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from typing import Literal

Kind = Literal["node", "start", "stop", "fork", "join"]
Agent = Literal["fresh", "inherit"]
Decision = Literal["true", "false"]
IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
SKILL = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*:[A-Za-z0-9_-][A-Za-z0-9_.-]*")


@dataclass(frozen=True)
class Node:
    """A graph declaration, with an optional subagent preference."""

    name: str
    target: str
    kind: Kind = "node"
    agent: Agent | None = None


@dataclass(frozen=True)
class Edge:
    """A directed edge; no condition means unconditional."""

    source: str
    target: str
    condition: str | None = None


@dataclass
class Workflow:
    """The parsed graph and its statically available resources."""

    filename: Path
    nodes: dict[str, Node]
    edges: list[Edge]
    joins: dict[str, str] = field(default_factory=dict)


def body(source: str) -> str:
    """Return Markdown after optional standard skill frontmatter."""
    return re.sub(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", "", source, count=1, flags=re.S).strip()


def flow_fields(source: str) -> list[str]:
    """Split a flow mapping without treating quoted or nested commas as fields."""
    fields: list[str] = []
    quote = ""
    depth = 0
    escaped = False
    start = 0
    for index, char in enumerate(source):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\" and quote == '"':
                escaped = True
            elif char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        elif char == "," and depth == 0:
            fields.append(source[start:index].strip())
            start = index + 1
    return fields + [source[start:].strip()]


def marked(source: str) -> bool:
    """Recognize the direct metadata.workflow marker, without a YAML dependency."""
    header = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", source, re.S)
    if header is None:
        return False
    lines = header[1].splitlines()
    marker = r"(?:workflow|'workflow'|\"workflow\"):\s*(?:mermaid-v1|'mermaid-v1'|\"mermaid-v1\")\s*(?:#.*)?"
    for index, line in enumerate(lines):
        if not line.startswith("metadata:"):
            continue
        value = line[len("metadata:"):].strip()
        if value.startswith("{") and "}" in value:
            return any(re.fullmatch(marker, item) for item in flow_fields(value[1:value.rfind("}")]))
        if value and not value.startswith("#"):
            return False
        children: list[str] = []
        for child in lines[index + 1:]:
            if child and not child[0].isspace():
                break
            if child.strip() and not child.lstrip().startswith("#"):
                children.append(child)
        if not children:
            return False
        indent = min(len(child) - len(child.lstrip()) for child in children)
        return any(len(child) - len(child.lstrip()) == indent and re.fullmatch(marker, child.strip()) for child in children)
    return False


def section(source: str, heading: str) -> str:
    """Read a level-two section while leaving ordinary Markdown unrestricted."""
    match = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", source, re.M | re.S)
    return match[1].strip() if match else ""


def node(line: str) -> Node | None:
    """Parse a Markdown path, skill reference, or requested control shape."""
    expanded = re.fullmatch(rf'({IDENTIFIER})@\{{ shape: (sm-circ|framed-circle|fork), label: "([^"]+)" \}}', line)
    if expanded:
        name, shape, label = expanded.groups()
        controls: dict[tuple[str, str], Kind] = {
            ("sm-circ", "Start"): "start", ("framed-circle", "Stop"): "stop",
            ("fork", "fork"): "fork", ("fork", "join"): "join",
        }
        kind = controls.get((shape, label))
        if kind is None or (kind == "start" and name != "_start") or (kind == "stop" and name != "_stop"):
            raise ValueError(f"Invalid control declaration: {line}")
        if name in {"_start", "_stop"} and kind not in {"start", "stop"}:
            raise ValueError(f"Reserved terminal identifier: {name}")
        return Node(name, f"{name}.md", kind)
    ordinary = re.fullmatch(rf'({IDENTIFIER})\["([^"<>`{{}}\\]+)"\]', line)
    if not ordinary:
        return None
    name, target = ordinary.groups()
    agent: Agent | None = None
    annotation = re.fullmatch(r"(.+) \[subagent:(fresh|inherit)\]", target)
    if annotation:
        target = annotation[1]
        agent = "fresh" if annotation[2] == "fresh" else "inherit"
    if "[subagent:" in target:
        raise ValueError("Use one [subagent:fresh] or [subagent:inherit] label suffix")
    if name in {"_start", "_stop"}:
        raise ValueError(f"Reserved terminal identifier: {name}")
    if not SKILL.fullmatch(target) and (Path(target).is_absolute() or ":" in target or not target.endswith(".md")):
        raise ValueError(f"Node {name} must name Markdown instructions or a plugin:skill reference")
    return Node(name, target, agent=agent)


def parse(filename: Path) -> Workflow:
    """Parse a graph-first workflow without loading or executing Mermaid."""
    source = filename.read_text(encoding="utf-8")
    if not marked(source):
        raise ValueError("Set metadata.workflow: mermaid-v1 in the skill frontmatter")
    entry = re.fullmatch(r"```mermaid\n(.*?)\n```(?:\s*\n## Notes\n(.*))?", body(source), re.S)
    if not entry:
        raise ValueError("Put the Mermaid graph first, followed only by optional Notes bullets")
    if entry[2] and any(line.strip() and not re.match(r"(?:[-*+] |\s+)", line) for line in entry[2].splitlines()):
        raise ValueError("Notes must be Markdown bullets")
    lines = [line.strip() for line in entry[1].splitlines() if line.strip()]
    if not lines or lines.pop(0) != "flowchart TD":
        raise ValueError("Use flowchart TD")
    workflow = Workflow(filename.resolve(), {}, [])
    for line in lines:
        current = node(line)
        if current:
            if current.name in workflow.nodes:
                raise ValueError(f"Duplicate node: {current.name}")
            workflow.nodes[current.name] = current
        elif line.startswith("%% ") and not line.startswith(("%% subagent", "%% agent ")):
            continue
        else:
            edge = re.fullmatch(rf'({IDENTIFIER}) -->(?:\|([^|"<>`{{}}\\]+)\|)? ({IDENTIFIER})', line)
            if not edge or (edge[2] is not None and not edge[2].strip()):
                raise ValueError(f"Unsupported Mermaid statement: {line}")
            workflow.edges.append(Edge(edge[1], edge[3], edge[2].strip() if edge[2] else None))
    validate_graph(workflow)
    return workflow


def reachable(start: str, edges: list[Edge], stop: str | None = None) -> set[str]:
    """Find reachable nodes without traversing beyond an optional join."""
    found: set[str] = set()
    pending = [start]
    while pending:
        current = pending.pop()
        if current == stop or current in found:
            continue
        found.add(current)
        pending.extend(edge.target for edge in edges if edge.source == current)
    return found


def validate_graph(workflow: Workflow) -> None:
    """Reject malformed topology, ambiguous branches, and conditional concurrency edges."""
    nodes, edges = workflow.nodes, workflow.edges
    if nodes.get("_start", Node("", "")).kind != "start" or nodes.get("_stop", Node("", "")).kind != "stop":
        raise ValueError("Declare _start and _stop with their Start and Stop shapes")
    for edge in edges:
        if edge.source not in nodes or edge.target not in nodes or edge.target == "_start" or edge.source == "_stop":
            raise ValueError(f"Invalid edge: {edge.source} -> {edge.target}")
        if edge.condition is not None and (nodes[edge.source].kind == "fork" or nodes[edge.target].kind == "join"):
            raise ValueError("Edges out of fork or into join must be unconditional")
    forward = reachable("_start", edges)
    reverse = reachable("_stop", [Edge(edge.target, edge.source) for edge in edges])
    for name, current in nodes.items():
        outgoing = [edge for edge in edges if edge.source == name]
        labels = [edge.condition for edge in outgoing]
        if name not in forward or name not in reverse:
            raise ValueError(f"Node must be reachable from start and able to reach stop: {name}")
        if len({edge.target for edge in outgoing}) != len(outgoing):
            raise ValueError(f"Duplicate branch target: {name}")
        if None in labels and any(label is not None for label in labels):
            raise ValueError(f"Cannot mix unconditional and conditional edges: {name}")
        if current.kind != "fork" and len(set(labels)) != len(labels):
            raise ValueError(f"Ambiguous outgoing edges: {name}")


def contained(filename: Path, root: Path) -> Path:
    """Resolve a regular file without allowing lexical or symlink escapes."""
    lexical = Path(filename.absolute())
    resolved = filename.resolve(strict=True)
    if not lexical.is_relative_to(root) or not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError(f"Reference leaves the bundle root: {filename}")
    return resolved


def instruction(workflow: Workflow, current: Node) -> Path:
    """Resolve instructions under steps/ or the reusable workflow's sibling directory."""
    directory = workflow.filename.parent.resolve()
    steps = "steps" if workflow.filename.name in {"SKILL.md", "WORKFLOW.md"} else workflow.filename.stem
    return contained(directory / steps / current.target, directory)


def skill_target(identifier: str, root: Path) -> Path | None:
    """Resolve known local skills; leave other identifiers to the executing harness."""
    plugin, name = identifier.split(":")
    candidates = [root / plugin / "skills"]
    if root.name == plugin:
        candidates.insert(0, root / "skills")
    if root.name == "skills" and root.parent.name == plugin:
        candidates.insert(0, root)
    for directory in candidates:
        if directory.is_dir():
            return contained(directory / name / "SKILL.md", root)
    return None


def validate_parallel(workflow: Workflow) -> None:
    """Use a fork's Join section to check branch separation and matching joins."""
    paired: set[str] = set()
    for name, current in workflow.nodes.items():
        if current.kind != "fork":
            continue
        join = section(instruction(workflow, current).read_text(encoding="utf-8"), "Join")
        if join not in workflow.nodes or workflow.nodes[join].kind != "join" or join in paired:
            raise ValueError(f"Fork {name} must name its matching join under ## Join")
        owners: dict[str, str] = {}
        for edge in workflow.edges:
            if edge.source != name:
                continue
            members = reachable(edge.target, workflow.edges, join)
            if not members:
                raise ValueError(f"Fork {name} cannot connect directly to its join")
            for member in members:
                if member in owners or workflow.nodes[member].kind in {"start", "stop"}:
                    raise ValueError(f"Branches overlap or bypass their join: {member}")
                owners[member] = edge.target
        for edge in workflow.edges:
            if edge.target in owners and edge.source != name and owners.get(edge.source) != owners[edge.target]:
                raise ValueError(f"Cross-branch entry: {edge.source} -> {edge.target}")
            if edge.target == join and edge.source not in owners:
                raise ValueError(f"Unexpected entry into join: {join}")
        workflow.joins[name] = join
        paired.add(join)
    if any(current.kind == "join" and name not in paired for name, current in workflow.nodes.items()):
        raise ValueError("Every join must belong to a fork")


def load(filename: Path, root: Path | None = None, seen: set[Path] | None = None) -> Workflow:
    """Validate local resources, including available nested workflows, without executing them."""
    root = (root or filename.resolve().parent).resolve(strict=True)
    filename = contained(filename, root)
    workflow = parse(filename)
    seen = seen if seen is not None else set()
    if filename in seen:
        return workflow
    seen.add(filename)
    for current in workflow.nodes.values():
        if SKILL.fullmatch(current.target):
            target = skill_target(current.target, root)
            if target is not None and marked(target.read_text(encoding="utf-8")):
                load(target, root, seen)
            continue
        target = instruction(workflow, current)
        document = target.read_text(encoding="utf-8")
        if not document.strip():
            raise ValueError(f"Empty Markdown instructions: {current.target}")
        if current.kind == "node" and marked(document):
            load(target, root, seen)
        heading = "Inputs" if current.kind == "start" else "Outputs" if current.kind == "stop" else None
        if heading and not re.search(r"^[-*+] \S", section(document, heading), re.M):
            raise ValueError(f"{current.name} needs {heading} bullets")
        if current.kind == "stop":
            template = section(document, "Output template")
            if template:
                contained(instruction(workflow, current).parent / template, filename.parent)
    validate_parallel(workflow)
    return workflow


def select(workflow: Workflow, name: str, decisions: dict[str, Decision]) -> list[Node]:
    """Select targets from agent assessments; forks dispatch every unconditional branch."""
    if name not in workflow.nodes:
        raise ValueError(f"Unknown node: {name}")
    outgoing = [edge for edge in workflow.edges if edge.source == name]
    conditional = {edge.target for edge in outgoing if edge.condition is not None}
    if set(decisions) - conditional:
        raise ValueError("Assess only conditional outgoing targets")
    if any(target not in decisions for target in conditional):
        raise ValueError("Assess every condition before navigation")
    selected = [edge for edge in outgoing if edge.condition is None or decisions.get(edge.target) == "true"]
    if not outgoing and workflow.nodes[name].kind == "stop":
        return []
    if not selected or (workflow.nodes[name].kind != "fork" and len(selected) != 1):
        raise ValueError("Blocked: select exactly one true condition")
    return [workflow.nodes[edge.target] for edge in selected]


class Parser(argparse.ArgumentParser):
    """Keep help off stdout so it remains a stream of navigation instructions."""

    def print_help(self, file: object = None) -> None:
        super().print_help(file=sys.stderr)


def run(arguments: list[str]) -> list[str]:
    """Return targets with any requested subagent instructions."""
    parser = Parser(description=__doc__)
    parser.add_argument("command", choices=("validate", "start", "next", "fork"))
    parser.add_argument("filename", type=Path)
    parser.add_argument("node", nargs="?")
    parser.add_argument("--root", type=Path)
    for value in ("true", "false"):
        parser.add_argument(f"--{value}", action="append", default=[], metavar="TARGET")
    args = parser.parse_args(arguments)
    decisions: dict[str, Decision] = {}
    for value in ("true", "false"):
        for target in getattr(args, value):
            if target in decisions:
                raise ValueError(f"Duplicate assessment: {target}")
            decisions[target] = "true" if value == "true" else "false"
    workflow = load(args.filename, args.root)
    if args.command in {"validate", "start"} and decisions:
        raise ValueError("Assessments apply only to next")
    if args.command == "validate":
        return []
    if args.command == "start":
        if args.node is not None:
            raise ValueError("start takes a workflow file, without a node")
        return [str(instruction(workflow, workflow.nodes["_start"]))]
    if args.node is None:
        raise ValueError(f"{args.command} requires a node")
    if args.node not in workflow.nodes:
        args.node = {"start": "_start", "stop": "_stop"}.get(args.node, args.node)
    if args.node not in workflow.nodes:
        raise ValueError(f"Unknown node: {args.node}")
    if args.command == "fork" and workflow.nodes[args.node].kind != "fork":
        raise ValueError(f"Not a fork: {args.node}")
    targets = select(workflow, args.node, decisions)
    results = []
    for current in targets:
        target = current.target if SKILL.fullmatch(current.target) else str(instruction(workflow, current))
        if current.agent == "fresh":
            target = f"Spawn a subagent with fresh context: {target}"
        elif current.agent == "inherit":
            target = f"Spawn a subagent inheriting the context from this thread: {target}"
        results.append(target)
    return results


def main() -> int:
    """Write navigation instructions to stdout and failures to stderr."""
    try:
        for target in run(sys.argv[1:]):
            print(target)
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
