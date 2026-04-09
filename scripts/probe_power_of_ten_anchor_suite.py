#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "KNOWN_PRIMES.md"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "power_of_ten_anchor_suite"
PLOTS_DIR = OUTPUT_DIR / "plots"
PYTHON_SRC = REPO_ROOT / "src" / "python"

if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from lpp import (  # noqa: E402
    cipolla_log5_repacked_seed,
    legacy_lpp_seed,
    li_inverse_seed,
    lpp_seed,
)


MIN_EXPONENT = 1
MAX_EXPONENT = 18
VARIANT_ORDER = [
    "lpp_seed",
    "legacy_lpp_seed",
    "cipolla_log5_repacked_seed",
    "li_inverse_seed",
]
VARIANT_LABELS = {
    "lpp_seed": "lpp_seed (official)",
    "legacy_lpp_seed": "legacy_lpp_seed",
    "cipolla_log5_repacked_seed": "cipolla_log5_repacked_seed",
    "li_inverse_seed": "li_inverse_seed",
}
VARIANT_COLORS = {
    "lpp_seed": "#c92a2a",
    "legacy_lpp_seed": "#1f77b4",
    "cipolla_log5_repacked_seed": "#0b7285",
    "li_inverse_seed": "#6741d9",
}
VARIANT_FUNCTIONS = {
    "lpp_seed": lpp_seed,
    "legacy_lpp_seed": legacy_lpp_seed,
    "cipolla_log5_repacked_seed": cipolla_log5_repacked_seed,
    "li_inverse_seed": li_inverse_seed,
}


def summarize(values: list[float]) -> dict[str, float]:
    array = np.array(values, dtype=np.float64)
    return {
        "max_rel_ppm": float(array.max()),
        "mean_rel_ppm": float(array.mean()),
        "median_rel_ppm": float(np.median(array)),
        "rms_rel_ppm": float(np.sqrt(np.mean(np.square(array)))),
    }


def load_power_of_ten_known_primes(path: Path) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    with path.open() as handle:
        for line in handle:
            if not line.startswith("|"):
                continue
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) < 4:
                continue
            try:
                n_value = int(parts[0].replace(",", "").replace("_", ""))
                p_n = int(parts[2].replace(",", "").replace("_", ""))
            except ValueError:
                continue
            exponent = len(str(n_value)) - 1
            if exponent < MIN_EXPONENT or exponent > MAX_EXPONENT:
                continue
            if n_value != 10**exponent:
                continue
            rows.append({"exponent": exponent, "n": n_value, "p_n": p_n})
    rows.sort(key=lambda row: int(row["exponent"]))
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_metric(
    rowwise_rows: list[dict[str, object]],
    metric_key: str,
    ylabel: str,
    title: str,
    filename: str,
) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.2), constrained_layout=True)
    for variant_name in VARIANT_ORDER:
        subset = [
            row
            for row in rowwise_rows
            if row["variant"] == variant_name and row["status"] == "ok"
        ]
        subset.sort(key=lambda row: int(row["exponent"]))
        ax.plot(
            [int(row["exponent"]) for row in subset],
            [float(row[metric_key]) for row in subset],
            marker="o",
            linewidth=2,
            color=VARIANT_COLORS[variant_name],
            label=VARIANT_LABELS[variant_name],
        )

    ax.set_yscale("log")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(list(range(MIN_EXPONENT, MAX_EXPONENT + 1)))
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(PLOTS_DIR / filename, dpi=180)
    plt.close(fig)


def plot_rank(rank_rows: list[dict[str, object]], filename: str) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.2), constrained_layout=True)
    for variant_name in VARIANT_ORDER:
        subset = [row for row in rank_rows if row["variant"] == variant_name]
        subset.sort(key=lambda row: int(row["exponent"]))
        ax.plot(
            [int(row["exponent"]) for row in subset],
            [int(row["rank"]) for row in subset],
            marker="o",
            linewidth=2,
            color=VARIANT_COLORS[variant_name],
            label=VARIANT_LABELS[variant_name],
        )

    ax.set_xlabel("log10(n)")
    ax.set_ylabel("rank")
    ax.set_title("Formula rank by exact power-of-ten anchor")
    ax.set_xticks(list(range(MIN_EXPONENT, MAX_EXPONENT + 1)))
    ax.set_yticks([1, 2, 3, 4])
    ax.set_ylim(4.2, 0.8)
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(PLOTS_DIR / filename, dpi=180)
    plt.close(fig)


def write_readme(
    exact_rows: list[dict[str, int]],
    summary_rows: list[dict[str, object]],
    best_rows: list[dict[str, object]],
) -> None:
    best_counts = {variant_name: 0 for variant_name in VARIANT_ORDER}
    tied_best_counts = {variant_name: 0 for variant_name in VARIANT_ORDER}
    for row in best_rows:
        winners = str(row["best_variants"]).split("|")
        if len(winners) == 1:
            best_counts[winners[0]] += 1
        if "lpp_seed" in winners:
            tied_best_counts["lpp_seed"] += 1

    official_best = best_counts["lpp_seed"]
    official_tied_best = tied_best_counts["lpp_seed"]
    lines = [
        "# Power-of-Ten Anchor Suite",
        "",
        "Official exact benchmark suite for the repository.",
        "",
        "This suite compares the four main formulas on `n = 10^1` through `10^18` using only exact power-of-ten anchors.",
        "",
        "Ground-truth provenance: [data/KNOWN_PRIMES.md](../../data/KNOWN_PRIMES.md)",
        "",
        "Formulas:",
        "- `lpp_seed`",
        "- `legacy_lpp_seed`",
        "- `cipolla_log5_repacked_seed`",
        "- `li_inverse_seed`",
        "",
        "Strongest supported finding:",
        f"- `lpp_seed` is sole best on `{official_best}` anchors and best-or-tied-best on `{official_tied_best}` anchors.",
        "- This runtime now uses the deterministic `r_inverse` construction as the shipped seed path.",
    ]
    lines.extend(
        [
            "",
            "Artifacts:",
            "- `rowwise_results.csv`: per-anchor per-formula exact results",
            "- `formula_summary.csv`: aggregate exact metrics by formula",
            "- `best_by_anchor.csv`: exact winner at each anchor",
            "- `rank_by_anchor.csv`: exact rank ordering at each anchor",
            "",
            "Status of older stage-based materials:",
            "- exact and local stage-based probes remain in the repository as supporting research artifacts",
            "- they are no longer the canonical benchmark surface for top-level summary or category decisions",
            "",
            "Plots:",
            "- `plots/anchor_rel_ppm.png`",
            "- `plots/anchor_abs_error.png`",
            "- `plots/anchor_rank.png`",
        ]
    )
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    exact_rows = load_power_of_ten_known_primes(DATA_PATH)
    rowwise_rows: list[dict[str, object]] = []
    for exact_row in exact_rows:
        exponent = int(exact_row["exponent"])
        n_value = int(exact_row["n"])
        p_n = int(exact_row["p_n"])
        for variant_name in VARIANT_ORDER:
            try:
                estimate = VARIANT_FUNCTIONS[variant_name](n_value)
                error = int(estimate) - p_n
                abs_error = abs(error)
                rel_ppm = abs_error / p_n * 1_000_000.0
                status = "ok"
            except Exception as exc:
                estimate = ""
                error = ""
                abs_error = ""
                rel_ppm = ""
                status = f"{type(exc).__name__}: {exc}"

            rowwise_rows.append(
                {
                    "exponent": exponent,
                    "n": n_value,
                    "variant": variant_name,
                    "estimate": estimate,
                    "p_n": p_n,
                    "error": error,
                    "abs_error": abs_error,
                    "rel_ppm": rel_ppm,
                    "status": status,
                }
            )

    summary_rows: list[dict[str, object]] = []
    for variant_name in VARIANT_ORDER:
        valid_rows = [
            row
            for row in rowwise_rows
            if row["variant"] == variant_name and row["status"] == "ok"
        ]
        rel_ppm_values = [float(row["rel_ppm"]) for row in valid_rows]
        abs_error_values = [int(row["abs_error"]) for row in valid_rows]
        metric_summary = summarize(rel_ppm_values)
        summary_rows.append(
            {
                "variant": variant_name,
                "valid_count": len(valid_rows),
                "max_rel_ppm": metric_summary["max_rel_ppm"],
                "mean_rel_ppm": metric_summary["mean_rel_ppm"],
                "median_rel_ppm": metric_summary["median_rel_ppm"],
                "rms_rel_ppm": metric_summary["rms_rel_ppm"],
                "max_abs_error": max(abs_error_values),
                "median_abs_error": int(np.median(np.array(abs_error_values, dtype=np.int64))),
            }
        )

    best_rows: list[dict[str, object]] = []
    rank_rows: list[dict[str, object]] = []
    for exact_row in exact_rows:
        exponent = int(exact_row["exponent"])
        n_value = int(exact_row["n"])
        valid_rows = [
            row
            for row in rowwise_rows
            if int(row["n"]) == n_value and row["status"] == "ok"
        ]
        valid_rows.sort(key=lambda row: float(row["rel_ppm"]))
        best_rel_ppm = float(valid_rows[0]["rel_ppm"])
        best_variants = [
            str(row["variant"])
            for row in valid_rows
            if math.isclose(float(row["rel_ppm"]), best_rel_ppm, rel_tol=0.0, abs_tol=1e-18)
        ]
        for rank, row in enumerate(valid_rows, start=1):
            rank_rows.append(
                {
                    "exponent": exponent,
                    "n": n_value,
                    "variant": row["variant"],
                    "rank": rank,
                    "rel_ppm": row["rel_ppm"],
                }
            )
        best = valid_rows[0]
        runner_up = valid_rows[1]
        best_rows.append(
            {
                "exponent": exponent,
                "n": n_value,
                "best_variant": best["variant"],
                "best_variants": "|".join(best_variants),
                "is_tie": len(best_variants) > 1,
                "best_rel_ppm": best["rel_ppm"],
                "runner_up_variant": runner_up["variant"],
                "runner_up_rel_ppm": runner_up["rel_ppm"],
                "winner_to_runner_up_ratio": float(best["rel_ppm"]) / float(runner_up["rel_ppm"]),
            }
        )

    write_csv(
        OUTPUT_DIR / "rowwise_results.csv",
        ["exponent", "n", "variant", "estimate", "p_n", "error", "abs_error", "rel_ppm", "status"],
        rowwise_rows,
    )
    write_csv(
        OUTPUT_DIR / "formula_summary.csv",
        ["variant", "valid_count", "max_rel_ppm", "mean_rel_ppm", "median_rel_ppm", "rms_rel_ppm", "max_abs_error", "median_abs_error"],
        summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "best_by_anchor.csv",
        ["exponent", "n", "best_variant", "best_variants", "is_tie", "best_rel_ppm", "runner_up_variant", "runner_up_rel_ppm", "winner_to_runner_up_ratio"],
        best_rows,
    )
    write_csv(
        OUTPUT_DIR / "rank_by_anchor.csv",
        ["exponent", "n", "variant", "rank", "rel_ppm"],
        rank_rows,
    )

    plot_metric(
        rowwise_rows,
        "rel_ppm",
        "seed ppm",
        "Exact power-of-ten anchor seed ppm",
        "anchor_rel_ppm.png",
    )
    plot_metric(
        rowwise_rows,
        "abs_error",
        "absolute seed error",
        "Exact power-of-ten anchor absolute seed error",
        "anchor_abs_error.png",
    )
    plot_rank(rank_rows, "anchor_rank.png")
    write_readme(exact_rows, summary_rows, best_rows)


if __name__ == "__main__":
    main()
