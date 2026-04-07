from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import gmpy2 as gp


REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_SRC = REPO_ROOT / "src" / "python"


def _parse_stage_name(argv: list[str]) -> str:
    stage_name = "baseline"
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--stage":
            stage_name = args[i + 1]
            i += 2
        else:
            raise SystemExit("usage: generate_held_out_exact_primes.py [--stage baseline|stage_a|stage_b|stage_c]")
    return stage_name


def _require_primecount_version() -> str:
    result = subprocess.run(
        ["primecount", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("primecount is required to generate the held-out exact dataset")
    return result.stdout.strip()


def main(argv: list[str]) -> int:
    if str(PYTHON_SRC) not in sys.path:
        sys.path.insert(0, str(PYTHON_SRC))

    from lpp.off_lattice_benchmark import (
        build_stage_specs,
        get_stage_spec,
        unique_index_runs,
        write_held_out_dataset,
    )

    stage_name = _parse_stage_name(argv)
    stage_spec = get_stage_spec(stage_name)
    dataset_path = REPO_ROOT / "data" / str(stage_spec["dataset"])
    manifest_path = REPO_ROOT / "data" / str(stage_spec["manifest"])

    oracle_version = _require_primecount_version()
    rows = build_stage_specs(stage_name)
    runs = unique_index_runs(rows)
    started_at = datetime.now(UTC).isoformat()

    n_to_prime: dict[int, int] = {}
    manifest_runs: list[dict[str, object]] = []
    command_template = "primecount {n} --nth-prime --threads=1"

    for run_index, run in enumerate(runs, start=1):
        start_n = int(run["start_n"])
        end_n = int(run["end_n"])
        n_values = [int(value) for value in run["n_values"]]
        command = ["primecount", str(start_n), "--nth-prime", "--threads=1"]
        t0 = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        anchor_elapsed = time.perf_counter() - t0
        if result.returncode != 0:
            raise SystemExit(
                f"primecount failed for n={start_n}: {result.stderr.strip() or result.stdout.strip()}"
            )
        current_prime = int(result.stdout.strip())
        n_to_prime[start_n] = current_prime
        for n_value in n_values[1:]:
            current_prime = int(gp.next_prime(current_prime))
            n_to_prime[n_value] = current_prime
        manifest_runs.append(
            {
                "run_index": run_index,
                "start_n": start_n,
                "end_n": end_n,
                "length": len(n_values),
                "anchor_command": " ".join(command),
                "anchor_elapsed_seconds": anchor_elapsed,
                "anchor_prime": n_to_prime[start_n],
                "method": "primecount anchor plus exact next_prime stepping",
            }
        )

    output_rows: list[dict[str, object]] = []
    for row in rows:
        output_row = dict(row)
        output_row["p_n"] = n_to_prime[int(row["n"])]
        output_rows.append(output_row)

    write_held_out_dataset(dataset_path, output_rows)
    manifest = {
        "stage": stage_name,
        "oracle": "primecount anchor plus gmpy2.next_prime stepping",
        "oracle_version": oracle_version,
        "gmpy2_version": gp.version(),
        "host": platform.platform(),
        "python": sys.version.split()[0],
        "started_at": started_at,
        "command_template": command_template,
        "row_count": len(output_rows),
        "run_count": len(manifest_runs),
        "runs": manifest_runs,
        "source": "local exact generation",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(dataset_path)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
