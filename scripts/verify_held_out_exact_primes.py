from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import gmpy2 as gp


REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_SRC = REPO_ROOT / "src" / "python"


def _parse_args(argv: list[str]) -> tuple[str, str | None, int | None]:
    stage_name = "baseline"
    family: str | None = None
    decade: int | None = None
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--stage":
            stage_name = args[i + 1]
            i += 2
        elif args[i] == "--family":
            family = args[i + 1]
            i += 2
        elif args[i] == "--decade":
            decade = int(args[i + 1])
            i += 2
        else:
            raise SystemExit(
                "usage: verify_held_out_exact_primes.py [--stage baseline|stage_a|stage_b|stage_c] [--family NAME] [--decade K]"
            )
    return stage_name, family, decade


def _require_primecount() -> None:
    version_result = subprocess.run(
        ["primecount", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if version_result.returncode != 0:
        raise SystemExit("primecount is required to verify the held-out exact dataset")


def main(argv: list[str]) -> int:
    if str(PYTHON_SRC) not in sys.path:
        sys.path.insert(0, str(PYTHON_SRC))

    from lpp.off_lattice_benchmark import get_stage_spec, parse_held_out_dataset, unique_index_runs

    stage_name, family, decade = _parse_args(argv)
    stage_spec = get_stage_spec(stage_name)
    _require_primecount()

    rows = parse_held_out_dataset(REPO_ROOT / "data" / str(stage_spec["dataset"]))
    if family is not None:
        rows = [row for row in rows if row["family"] == family]
    if decade is not None:
        rows = [row for row in rows if int(row["decade_exponent"]) == decade]
    if not rows:
        raise SystemExit("no rows matched the requested verification filter")

    expected_by_n = {int(row["n"]): int(row["p_n"]) for row in rows}
    runs = unique_index_runs(rows)
    for run in runs:
        start_n = int(run["start_n"])
        n_values = [int(value) for value in run["n_values"]]
        result = subprocess.run(
            ["primecount", str(start_n), "--nth-prime", "--threads=1"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(
                f"primecount failed for n={start_n}: {result.stderr.strip() or result.stdout.strip()}"
            )
        current_prime = int(result.stdout.strip())
        if current_prime != expected_by_n[start_n]:
            raise SystemExit(f"mismatch for n={start_n}: got {current_prime}, expected {expected_by_n[start_n]}")
        for n_value in n_values[1:]:
            current_prime = int(gp.next_prime(current_prime))
            expected = expected_by_n[n_value]
            if current_prime != expected:
                raise SystemExit(f"mismatch for n={n_value}: got {current_prime}, expected {expected}")

    print("verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
