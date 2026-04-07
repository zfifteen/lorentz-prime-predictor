from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    python_src = repo_root / "src" / "python"
    if str(python_src) not in sys.path:
        sys.path.insert(0, str(python_src))

    from lpp.off_lattice_benchmark import write_off_lattice_benchmark_artifacts

    artifacts = write_off_lattice_benchmark_artifacts(repo_root)
    print(artifacts["csv"])
    print(artifacts["summary"])
    print(artifacts["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
