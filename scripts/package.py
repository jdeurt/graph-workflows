"""Package the single skill through Soubi, excluding repository contributor files."""

from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory


def main() -> None:
    """Build native Claude Code and Codex bundles without a marketplace."""
    root = Path(__file__).resolve().parent.parent
    with TemporaryDirectory(prefix="graph-workflows-") as temporary:
        source = Path(temporary) / "graph-workflows"
        shutil.copytree(root / "skills", source / "skills")
        subprocess.run(
            ["npx", "--yes", "soubi@0.0.1", "build", str(source),
             "--harness", "claude,codex", "--strict", "--out", str(root / ".soubi-out")],
            check=True,
        )


if __name__ == "__main__":
    main()
