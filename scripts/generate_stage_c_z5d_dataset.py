from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_SRC = REPO_ROOT / "src" / "python"
Z5D_ROOT = Path("/Users/velocityworks/IdeaProjects/archive/z5d-prime-predictor/src/c/z5d-predictor-c")
Z5D_CLI = Z5D_ROOT / "bin" / "z5d_cli"
STAGE_NAME = "stage_c"
PREDICTED_PRIME_PATTERN = re.compile(r"Predicted prime:\s*([0-9]+)")


def _require_z5d_cli() -> None:
    if not Z5D_CLI.exists():
        raise SystemExit(
            f"missing Z5D CLI at {Z5D_CLI}. Build it with `make cli` in {Z5D_ROOT} before generating stage_c."
        )


def _predict_with_z5d(n_value: int) -> tuple[int, float]:
    started = time.perf_counter()
    result = subprocess.run(
        [str(Z5D_CLI), str(n_value)],
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise SystemExit(
            f"z5d_cli failed for n={n_value}: {result.stderr.strip() or result.stdout.strip()}"
        )
    match = PREDICTED_PRIME_PATTERN.search(result.stdout)
    if match is None:
        raise SystemExit(f"could not parse predicted prime for n={n_value}: {result.stdout.strip()}")
    return int(match.group(1)), elapsed


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        raise SystemExit("usage: generate_stage_c_z5d_dataset.py")

    if str(PYTHON_SRC) not in sys.path:
        sys.path.insert(0, str(PYTHON_SRC))

    from lpp.off_lattice_benchmark import build_stage_specs, get_stage_spec, write_held_out_dataset

    _require_z5d_cli()
    stage_spec = get_stage_spec(STAGE_NAME)
    dataset_path = REPO_ROOT / "data" / str(stage_spec["dataset"])
    manifest_path = REPO_ROOT / "data" / str(stage_spec["manifest"])

    rows = build_stage_specs(STAGE_NAME)
    unique_n_values = sorted({int(row["n"]) for row in rows})
    predicted_by_n: dict[int, int] = {}
    timing_rows: list[dict[str, object]] = []

    for index, n_value in enumerate(unique_n_values, start=1):
        predicted_prime, elapsed = _predict_with_z5d(n_value)
        predicted_by_n[n_value] = predicted_prime
        timing_rows.append(
            {
                "index": index,
                "n": n_value,
                "predicted_prime": predicted_prime,
                "elapsed_seconds": elapsed,
            }
        )

    output_rows: list[dict[str, object]] = []
    for row in rows:
        output_row = dict(row)
        output_row["p_n"] = predicted_by_n[int(row["n"])]
        output_rows.append(output_row)

    write_held_out_dataset(dataset_path, output_rows)

    elapsed_values = [float(row["elapsed_seconds"]) for row in timing_rows]
    manifest = {
        "stage": STAGE_NAME,
        "source": "workspace_z5d_c_predictor",
        "source_kind": "z5d_c_local",
        "z5d_cli": str(Z5D_CLI),
        "row_count": len(output_rows),
        "unique_n_count": len(unique_n_values),
        "mean_prediction_seconds": sum(elapsed_values) / len(elapsed_values),
        "max_prediction_seconds": max(elapsed_values),
        "runs": timing_rows,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(dataset_path)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
