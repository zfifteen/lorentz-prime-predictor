from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import gmpy2 as gp


REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_SRC = REPO_ROOT / "src" / "python"
PRIMECOUNT = "primecount"
STAGE_NAME = "stage_c"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "stage_c_exact_primecount"


def _require_primecount() -> None:
    result = subprocess.run(
        [PRIMECOUNT, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("primecount is not available on PATH")


def _nth_prime_primecount(n_value: int) -> tuple[int, float]:
    command = [PRIMECOUNT, str(n_value), "--nth-prime", "--threads=1"]
    started = time.perf_counter()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"primecount failed for n={n_value}: {message}")
    try:
        return int(result.stdout.strip()), elapsed
    except ValueError as exc:
        raise SystemExit(f"could not parse primecount output for n={n_value}: {result.stdout!r}") from exc


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _run_rows_for_indices(stage_rows: list[dict[str, int | str]], n_values: list[int]) -> list[dict[str, object]]:
    unique_stage_rows = [row for row in stage_rows if int(row["n"]) in set(n_values)]
    anchor_n = min(n_values)
    anchor_prime, anchor_elapsed = _nth_prime_primecount(anchor_n)

    predicted_by_n: dict[int, int] = {anchor_n: anchor_prime}
    current_prime = anchor_prime
    current_n = anchor_n
    for target_n in sorted(n for n in n_values if n > anchor_n):
        while current_n < target_n:
            current_prime = int(gp.next_prime(current_prime))
            current_n += 1
        predicted_by_n[target_n] = current_prime

    output_rows: list[dict[str, object]] = []
    for row in unique_stage_rows:
        output_row = dict(row)
        output_row["p_n"] = predicted_by_n[int(row["n"])]
        output_rows.append(output_row)

    output_rows.sort(key=lambda row: (int(row["n"]), str(row["family"]), str(row["row_id"])))
    return output_rows, anchor_prime, anchor_elapsed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Generate exact stage_c rows using primecount anchors and deterministic next_prime stepping."
    )
    parser.add_argument(
        "--run-index",
        type=int,
        default=1,
        help="1-based run index within stage_c contiguous unique-n runs.",
    )
    args = parser.parse_args(argv[1:])

    if str(PYTHON_SRC) not in sys.path:
        sys.path.insert(0, str(PYTHON_SRC))

    from lpp.off_lattice_benchmark import build_stage_specs, unique_index_runs

    _require_primecount()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stage_rows = build_stage_specs(STAGE_NAME)
    runs = unique_index_runs(stage_rows)
    run_index = args.run_index
    if run_index < 1 or run_index > len(runs):
        raise SystemExit(f"run-index must be between 1 and {len(runs)}")

    selected_run = runs[run_index - 1]
    n_values = [int(value) for value in selected_run["n_values"]]
    output_rows, anchor_prime, anchor_elapsed = _run_rows_for_indices(stage_rows, n_values)

    csv_path = OUTPUT_DIR / f"stage_c_run_{run_index:02d}.csv"
    manifest_path = OUTPUT_DIR / f"stage_c_run_{run_index:02d}_manifest.json"
    _write_csv(
        csv_path,
        ["row_id", "family", "decade_exponent", "n", "p_n"],
        output_rows,
    )
    manifest = {
        "stage": STAGE_NAME,
        "run_index": run_index,
        "start_n": selected_run["start_n"],
        "end_n": selected_run["end_n"],
        "length": selected_run["length"],
        "anchor_n": n_values[0],
        "anchor_prime": anchor_prime,
        "anchor_command": f"{PRIMECOUNT} {n_values[0]} --nth-prime --threads=1",
        "anchor_elapsed_seconds": anchor_elapsed,
        "method": "primecount anchor plus exact next_prime stepping",
        "row_count": len(output_rows),
        "source": "local exact generation",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(csv_path)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
