#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "benchmarks" / "gwr_hybrid_probe" / "rowwise_results.csv"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "gwr_trapped_interval"
PLOTS_DIR = OUTPUT_DIR / "plots"
PYTHON_SRC = REPO_ROOT / "src" / "python"

if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from lpp.predictor import lpp_refined_predictor  # noqa: E402


TARGET_VARIANT = "r_inverse_seed"
TARGET_FAMILIES = {"boundary_window", "dense_local_window", "published_exact_grid"}


def major_zone(n_value: int, decade_exponent: int) -> str:
    mantissa = n_value / (10**decade_exponent)
    if 0.49 <= mantissa <= 0.51:
        return "mant_0.5"
    if 0.89 <= mantissa <= 0.91:
        return "mant_0.9"
    if 0.999 <= mantissa <= 1.0011:
        return "mant_1.0"
    return "other"


def percentile(values: list[int], pct: float) -> int:
    if not values:
        raise ValueError("values must be non-empty")
    return int(np.percentile(np.array(values, dtype=float), pct))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_method_stats(summary_rows: list[dict[str, object]]) -> None:
    labels = [row["method"] for row in summary_rows]
    medians = [int(row["median"]) for row in summary_rows]
    p90s = [int(row["p90"]) for row in summary_rows]
    maximums = [int(row["max"]) for row in summary_rows]

    fig, ax = plt.subplots(figsize=(9.8, 5.0))
    x = np.arange(len(labels))
    width = 0.26
    ax.bar(x - width, medians, width=width, color="#0b7285", label="median")
    ax.bar(x, p90s, width=width, color="#74c0fc", label="p90")
    ax.bar(x + width, maximums, width=width, color="#c92a2a", label="max")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_yscale("log")
    ax.set_ylabel("Absolute error or interval width")
    ax.set_title("Trapped interval versus existing point predictors")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "method_scale_comparison.png", dpi=200)
    plt.close(fig)


def plot_interval_width_by_class(class_rows: list[dict[str, object]]) -> None:
    labels = [f"{row['decade_exponent']}:{row['zone']}" for row in class_rows]
    widths = [int(row["interval_width"]) for row in class_rows]

    fig, ax = plt.subplots(figsize=(12.2, 5.0))
    ax.bar(np.arange(len(class_rows)), widths, color="#0b7285")
    ax.set_xticks(np.arange(len(class_rows)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yscale("log")
    ax.set_ylabel("Exact trapped interval width")
    ax.set_title("Class-conditioned trapped interval widths for r_inverse_seed")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "interval_width_by_class.png", dpi=200)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    unique_rows: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    with INPUT_PATH.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["variant"] != TARGET_VARIANT:
                continue
            if row["family"] not in TARGET_FAMILIES:
                continue
            key = (row["dataset"], int(row["n"]))
            if key in seen:
                continue
            seen.add(key)
            unique_rows.append(
                {
                    "dataset": row["dataset"],
                    "family": row["family"],
                    "decade_exponent": int(row["decade_exponent"]),
                    "n": int(row["n"]),
                    "p_n": int(row["p_n"]),
                    "seed": int(row["seed"]),
                    "seed_minus_winner": int(row["seed_minus_winner"]),
                    "prime_minus_winner": int(row["prime_minus_winner"]),
                }
            )

    offsets_by_class: dict[tuple[int, str], list[int]] = defaultdict(list)
    tails_by_class: dict[tuple[int, str], list[int]] = defaultdict(list)
    for row in unique_rows:
        class_key = (int(row["decade_exponent"]), major_zone(int(row["n"]), int(row["decade_exponent"])))
        offsets_by_class[class_key].append(int(row["seed_minus_winner"]))
        tails_by_class[class_key].append(int(row["prime_minus_winner"]))

    class_rows: list[dict[str, object]] = []
    class_interval: dict[tuple[int, str], tuple[int, int, int]] = {}
    for class_key in sorted(offsets_by_class):
        offsets = sorted(offsets_by_class[class_key])
        tails = sorted(tails_by_class[class_key])
        min_offset = offsets[0]
        max_offset = offsets[-1]
        tail_max = tails[-1]
        interval_width = (max_offset - min_offset) + tail_max
        class_interval[class_key] = (min_offset, max_offset, tail_max)
        class_rows.append(
            {
                "decade_exponent": class_key[0],
                "zone": class_key[1],
                "row_count": len(offsets),
                "min_offset": min_offset,
                "max_offset": max_offset,
                "tail_max": tail_max,
                "interval_width": interval_width,
                "median_tail": int(np.median(np.array(tails, dtype=float))),
                "p95_tail": percentile(tails, 95),
            }
        )

    rowwise_results: list[dict[str, object]] = []
    interval_widths: list[int] = []
    interval_odd_counts: list[int] = []
    r_inverse_errors: list[int] = []
    lpp_refined_errors: list[int] = []
    shrink_ratios_vs_r: list[float] = []
    shrink_ratios_vs_lpp: list[float] = []

    for row in unique_rows:
        class_key = (int(row["decade_exponent"]), major_zone(int(row["n"]), int(row["decade_exponent"])))
        min_offset, max_offset, tail_max = class_interval[class_key]
        seed = int(row["seed"])
        p_n = int(row["p_n"])
        interval_lo = seed - max_offset
        interval_hi = seed - min_offset + tail_max
        interval_width = interval_hi - interval_lo
        interval_odd_count = ((interval_hi - interval_lo) // 2) + 1
        contains_true_prime = int(interval_lo <= p_n <= interval_hi)
        r_inverse_error = abs(seed - p_n)
        refined = lpp_refined_predictor(int(row["n"]))
        lpp_refined_error = abs(refined - p_n)

        interval_widths.append(interval_width)
        interval_odd_counts.append(interval_odd_count)
        r_inverse_errors.append(r_inverse_error)
        lpp_refined_errors.append(lpp_refined_error)
        shrink_ratios_vs_r.append(r_inverse_error / interval_width)
        shrink_ratios_vs_lpp.append(lpp_refined_error / interval_width)

        rowwise_results.append(
            {
                "dataset": row["dataset"],
                "family": row["family"],
                "decade_exponent": row["decade_exponent"],
                "zone": class_key[1],
                "n": row["n"],
                "p_n": p_n,
                "r_inverse_seed": seed,
                "r_inverse_abs_error": r_inverse_error,
                "lpp_refined_predictor": refined,
                "lpp_refined_abs_error": lpp_refined_error,
                "interval_lo": interval_lo,
                "interval_hi": interval_hi,
                "interval_width": interval_width,
                "interval_odd_count": interval_odd_count,
                "contains_true_prime": contains_true_prime,
                "shrink_ratio_vs_r_inverse": f"{r_inverse_error / interval_width:.6f}",
                "shrink_ratio_vs_lpp_refined": f"{lpp_refined_error / interval_width:.6f}",
            }
        )

    method_summary = [
        {
            "method": "trapped_interval_width",
            "median": int(np.median(np.array(interval_widths, dtype=float))),
            "p90": percentile(interval_widths, 90),
            "max": max(interval_widths),
        },
        {
            "method": "trapped_interval_odd_count",
            "median": int(np.median(np.array(interval_odd_counts, dtype=float))),
            "p90": percentile(interval_odd_counts, 90),
            "max": max(interval_odd_counts),
        },
        {
            "method": "r_inverse_abs_error",
            "median": int(np.median(np.array(r_inverse_errors, dtype=float))),
            "p90": percentile(r_inverse_errors, 90),
            "max": max(r_inverse_errors),
        },
        {
            "method": "lpp_refined_abs_error",
            "median": int(np.median(np.array(lpp_refined_errors, dtype=float))),
            "p90": percentile(lpp_refined_errors, 90),
            "max": max(lpp_refined_errors),
        },
    ]

    interval_summary = [
        {
            "row_count": len(rowwise_results),
            "exact_coverage_rate": f"{np.mean([row['contains_true_prime'] for row in rowwise_results]):.6f}",
            "median_interval_width": int(np.median(np.array(interval_widths, dtype=float))),
            "p90_interval_width": percentile(interval_widths, 90),
            "max_interval_width": max(interval_widths),
            "median_interval_odd_count": int(np.median(np.array(interval_odd_counts, dtype=float))),
            "p90_interval_odd_count": percentile(interval_odd_counts, 90),
            "max_interval_odd_count": max(interval_odd_counts),
            "median_shrink_ratio_vs_r_inverse": f"{np.median(np.array(shrink_ratios_vs_r, dtype=float)):.6f}",
            "p90_shrink_ratio_vs_r_inverse": f"{np.percentile(np.array(shrink_ratios_vs_r, dtype=float), 90):.6f}",
            "median_shrink_ratio_vs_lpp_refined": f"{np.median(np.array(shrink_ratios_vs_lpp, dtype=float)):.6f}",
            "p90_shrink_ratio_vs_lpp_refined": f"{np.percentile(np.array(shrink_ratios_vs_lpp, dtype=float), 90):.6f}",
        }
    ]

    write_csv(
        OUTPUT_DIR / "class_interval_summary.csv",
        [
            "decade_exponent",
            "zone",
            "row_count",
            "min_offset",
            "max_offset",
            "tail_max",
            "interval_width",
            "median_tail",
            "p95_tail",
        ],
        class_rows,
    )
    write_csv(
        OUTPUT_DIR / "rowwise_interval_results.csv",
        [
            "dataset",
            "family",
            "decade_exponent",
            "zone",
            "n",
            "p_n",
            "r_inverse_seed",
            "r_inverse_abs_error",
            "lpp_refined_predictor",
            "lpp_refined_abs_error",
            "interval_lo",
            "interval_hi",
            "interval_width",
            "interval_odd_count",
            "contains_true_prime",
            "shrink_ratio_vs_r_inverse",
            "shrink_ratio_vs_lpp_refined",
        ],
        rowwise_results,
    )
    write_csv(
        OUTPUT_DIR / "method_summary.csv",
        ["method", "median", "p90", "max"],
        method_summary,
    )
    write_csv(
        OUTPUT_DIR / "interval_summary.csv",
        [
            "row_count",
            "exact_coverage_rate",
            "median_interval_width",
            "p90_interval_width",
            "max_interval_width",
            "median_interval_odd_count",
            "p90_interval_odd_count",
            "max_interval_odd_count",
            "median_shrink_ratio_vs_r_inverse",
            "p90_shrink_ratio_vs_r_inverse",
            "median_shrink_ratio_vs_lpp_refined",
            "p90_shrink_ratio_vs_lpp_refined",
        ],
        interval_summary,
    )

    plot_method_stats(method_summary)
    plot_interval_width_by_class(class_rows)


if __name__ == "__main__":
    main()
