from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    python_src = repo_root / "src" / "python"
    if str(python_src) not in sys.path:
        sys.path.insert(0, str(python_src))

    from lpp.off_lattice_benchmark import write_off_lattice_benchmark_artifacts

    stage_names: list[str] = []
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--stage":
            stage_names.append(args[i + 1])
            i += 2
        else:
            raise SystemExit("usage: run_off_lattice_benchmark.py [--stage NAME ...]")

    artifacts = write_off_lattice_benchmark_artifacts(repo_root, stage_names or None)
    print(artifacts["csv"])
    print(artifacts["summary"])
    print(artifacts["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
