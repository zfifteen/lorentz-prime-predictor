from __future__ import annotations

import csv
import json
from pathlib import Path

from .predictor import lpp_refined_predictor, lpp_seed


def _parse_known_primes(path: Path) -> list[tuple[int, int]]:
    rows: list[tuple[int, int]] = []
    for line in path.read_text().splitlines():
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 3:
            continue
        try:
            n_value = int(parts[0].replace(",", "").replace("_", ""))
            p_value = int(parts[2].replace(",", "").replace("_", ""))
        except ValueError:
            continue
        rows.append((n_value, p_value))
    if not rows:
        raise ValueError(f"no benchmark rows parsed from {path}")
    return rows


def _band_label(n: int) -> str:
    exponent = len(str(n)) - 1
    return f"10^{exponent}"


def build_contract_grid_rows(known_primes_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for n_value, p_value in _parse_known_primes(known_primes_path):
        seed = lpp_seed(n_value)
        refined = lpp_refined_predictor(n_value)
        seed_error = seed - p_value
        refined_error = refined - p_value
        seed_rel_ppm = abs(seed_error) / p_value * 1e6
        refined_rel_ppm = abs(refined_error) / p_value * 1e6
        exact_match = refined == p_value

        row = {
            "band": _band_label(n_value),
            "n": n_value,
            "p_n": p_value,
            "lpp_seed": seed,
            "lpp_seed_error": seed_error,
            "lpp_seed_rel_ppm": f"{seed_rel_ppm:.12f}",
            "lpp_refined_predictor": refined,
            "lpp_refined_error": refined_error,
            "lpp_refined_rel_ppm": f"{refined_rel_ppm:.12f}",
            "exact_match": exact_match,
        }
        rows.append(row)

    failures = [row for row in rows if not row["exact_match"]]
    if failures:
        first = failures[0]
        raise ValueError(
            "contract grid exact-match failure at "
            f"n={first['n']}: got {first['lpp_refined_predictor']}, expected {first['p_n']}"
        )

    return rows


def write_contract_grid_artifacts(repo_root: Path, output_dir: Path | None = None) -> dict[str, Path]:
    known_primes_path = repo_root / "data" / "KNOWN_PRIMES.md"
    benchmark_dir = output_dir if output_dir is not None else repo_root / "benchmarks"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    rows = build_contract_grid_rows(known_primes_path)
    csv_path = benchmark_dir / "contract_grid.csv"
    md_path = benchmark_dir / "contract_grid.md"
    summary_path = benchmark_dir / "summary_bands.json"

    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "band",
                "n",
                "p_n",
                "lpp_seed",
                "lpp_seed_error",
                "lpp_seed_rel_ppm",
                "lpp_refined_predictor",
                "lpp_refined_error",
                "lpp_refined_rel_ppm",
                "exact_match",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    summary_rows: list[dict[str, object]] = []
    for row in rows:
        band_path = benchmark_dir / f"band_{str(row['band']).replace('^', '_')}.json"
        band_payload = {
            "band": row["band"],
            "n": row["n"],
            "p_n": str(row["p_n"]),
            "lpp": {
                "seed": str(row["lpp_seed"]),
                "seed_error": row["lpp_seed_error"],
                "seed_rel_ppm": row["lpp_seed_rel_ppm"],
                "refined_predictor": str(row["lpp_refined_predictor"]),
                "refined_error": row["lpp_refined_error"],
                "refined_rel_ppm": row["lpp_refined_rel_ppm"],
                "exact_match": row["exact_match"],
            },
        }
        band_path.write_text(json.dumps(band_payload, indent=2) + "\n")
        summary_rows.append(band_payload)

    summary_path.write_text(json.dumps(summary_rows, indent=2) + "\n")

    worst_seed = sorted(
        rows,
        key=lambda row: (
            float(str(row["lpp_seed_rel_ppm"])),
            int(row["n"]),
        ),
        reverse=True,
    )[:3]
    md_lines = [
        "# Contract Grid Benchmark",
        "",
        "Exact contract result: `lpp_refined_predictor(n)` matches the deterministic ground-truth grid at every declared band from $10^0$ through $10^{24}$.",
        "",
        "## Summary",
        "",
        f"- bands evaluated: {len(rows)}",
        f"- refined exact matches: {sum(1 for row in rows if row['exact_match'])}/{len(rows)}",
        f"- max refined ppm: {max(float(str(row['lpp_refined_rel_ppm'])) for row in rows):.12f}",
        f"- max seed ppm: {max(float(str(row['lpp_seed_rel_ppm'])) for row in rows):.12f}",
        "",
        "## Worst Seed Rows",
        "",
        "| Band | n | p_n | Seed | Seed error | Seed ppm | Refined | Exact match |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for row in worst_seed:
        md_lines.append(
            f"| {row['band']} | {row['n']} | {row['p_n']} | {row['lpp_seed']} | "
            f"{row['lpp_seed_error']} | {row['lpp_seed_rel_ppm']} | "
            f"{row['lpp_refined_predictor']} | {row['exact_match']} |"
        )
    md_lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- CSV: `{csv_path.name}`",
            f"- Summary JSON: `{summary_path.name}`",
            "- Per-band JSON: `band_10_0.json` through `band_10_24.json`",
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n")

    return {
        "csv": csv_path,
        "markdown": md_path,
        "summary": summary_path,
    }
