#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "benchmarks" / "gwr_hybrid_probe" / "rowwise_results.csv"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "gwr_prime_band_holdout"
PLOTS_DIR = OUTPUT_DIR / "plots"

TARGET_VARIANT = "r_inverse_seed"
TARGET_FAMILIES = {"boundary_window", "dense_local_window"}
TRAIN_FRACTION_NUM = 2
TRAIN_FRACTION_DEN = 3


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


def enumerate_primes(interval_lo: int, interval_hi: int) -> list[int]:
    primes: list[int] = []
    current = int(gp.next_prime(interval_lo - 1))
    while current <= interval_hi:
        primes.append(current)
        current = int(gp.next_prime(current))
    return primes


def plot_method_comparison(summary_rows: list[dict[str, object]]) -> None:
    labels = [row["method"] for row in summary_rows]
    coverages = [float(row["test_coverage_rate"]) for row in summary_rows]
    widths = [int(row["median_interval_width"]) for row in summary_rows]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.8, 4.8))
    x = np.arange(len(labels))

    ax1.bar(x, coverages, color=["#0b7285", "#c92a2a"])
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=15, ha="right")
    ax1.set_ylim(0.0, 1.0)
    ax1.set_ylabel("Holdout coverage rate")
    ax1.set_title("Coverage on held-out upper-third rows")
    ax1.grid(axis="y", alpha=0.25)

    ax2.bar(x, widths, color=["#0b7285", "#c92a2a"])
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=15, ha="right")
    ax2.set_ylabel("Median interval width")
    ax2.set_title("Holdout interval width")
    ax2.grid(axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "holdout_method_comparison.png", dpi=200)
    plt.close(fig)


def plot_constant_coverage_by_class(class_rows: list[dict[str, object]]) -> None:
    rows = [row for row in class_rows if row["method"] == "constant_band"]
    labels = [f"{row['decade_exponent']}:{row['zone']}" for row in rows]
    coverages = [float(row["test_coverage_rate"]) for row in rows]

    fig, ax = plt.subplots(figsize=(12.6, 5.0))
    ax.bar(np.arange(len(rows)), coverages, color="#0b7285")
    ax.set_xticks(np.arange(len(rows)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Holdout coverage rate")
    ax.set_title("Constant class band coverage on held-out upper-third rows")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "constant_band_coverage_by_class.png", dpi=200)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, int | str]] = []
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
            decade_exponent = int(row["decade_exponent"])
            n_value = int(row["n"])
            seed = int(row["seed"])
            p_n = int(row["p_n"])
            rows.append(
                {
                    "dataset": row["dataset"],
                    "family": row["family"],
                    "decade_exponent": decade_exponent,
                    "zone": major_zone(n_value, decade_exponent),
                    "n": n_value,
                    "seed": seed,
                    "p_n": p_n,
                    "prime_offset": seed - p_n,
                }
            )

    grouped: dict[tuple[int, str], list[dict[str, int | str]]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["decade_exponent"]), str(row["zone"]))].append(row)

    rowwise_rows: list[dict[str, object]] = []
    class_rows: list[dict[str, object]] = []
    per_method_coverages: dict[str, list[int]] = defaultdict(list)
    per_method_widths: dict[str, list[int]] = defaultdict(list)
    per_method_prime_counts: dict[str, list[int]] = defaultdict(list)
    per_method_checks: dict[str, list[int]] = defaultdict(list)
    per_method_top1: dict[str, int] = defaultdict(int)
    per_method_top3: dict[str, int] = defaultdict(int)
    per_method_top5: dict[str, int] = defaultdict(int)
    per_method_empty: dict[str, int] = defaultdict(int)
    per_method_abs_error: dict[str, list[int]] = defaultdict(list)
    per_method_test_count: dict[str, int] = defaultdict(int)

    for class_key in sorted(grouped):
        class_rows_sorted = sorted(grouped[class_key], key=lambda row: int(row["n"]))
        cut = max(1, math.floor(len(class_rows_sorted) * TRAIN_FRACTION_NUM / TRAIN_FRACTION_DEN))
        if cut >= len(class_rows_sorted):
            cut = len(class_rows_sorted) - 1
        train_rows = class_rows_sorted[:cut]
        test_rows = class_rows_sorted[cut:]
        train_offsets = [int(row["prime_offset"]) for row in train_rows]

        constant_lo = min(train_offsets)
        constant_hi = max(train_offsets)
        constant_center = int(np.median(np.array(train_offsets, dtype=float)))

        x_train = np.arange(len(train_rows), dtype=float)
        y_train = np.array(train_offsets, dtype=float)
        if len(train_rows) >= 2:
            slope, intercept = np.polyfit(x_train, y_train, 1)
        else:
            slope, intercept = 0.0, y_train[0]
        train_residuals = [
            int(round(int(row["prime_offset"]) - (slope * index + intercept)))
            for index, row in enumerate(train_rows)
        ]
        linear_lo = min(train_residuals)
        linear_hi = max(train_residuals)

        method_local = {
            "constant_band": {
                "coverage": 0,
                "empty_intervals": 0,
                "widths": [],
                "prime_counts": [],
                "checks": [],
                "errors": [],
                "top1": 0,
                "top3": 0,
                "top5": 0,
            },
            "linear_band": {
                "coverage": 0,
                "empty_intervals": 0,
                "widths": [],
                "prime_counts": [],
                "checks": [],
                "errors": [],
                "top1": 0,
                "top3": 0,
                "top5": 0,
            },
        }

        for test_index, row in enumerate(test_rows, start=len(train_rows)):
            seed = int(row["seed"])
            p_n = int(row["p_n"])

            constant_interval_lo = seed - constant_hi
            constant_interval_hi = seed - constant_lo
            constant_primes = enumerate_primes(constant_interval_lo, constant_interval_hi)
            constant_target = seed - constant_center
            constant_ordered = sorted(constant_primes, key=lambda value: (abs(value - constant_target), value))
            constant_contains = int(constant_interval_lo <= p_n <= constant_interval_hi)
            constant_width = constant_interval_hi - constant_interval_lo
            constant_prime_count = len(constant_primes)
            method_local["constant_band"]["widths"].append(constant_width)
            method_local["constant_band"]["prime_counts"].append(constant_prime_count)

            if not constant_primes:
                constant_checks = ""
                constant_prediction = ""
                constant_abs_error = ""
                method_local["constant_band"]["empty_intervals"] += 1
            elif constant_contains:
                constant_checks = constant_ordered.index(p_n) + 1
                constant_prediction = constant_ordered[0]
                constant_abs_error = abs(constant_prediction - p_n)
                method_local["constant_band"]["coverage"] += 1
                method_local["constant_band"]["checks"].append(constant_checks)
                method_local["constant_band"]["errors"].append(constant_abs_error)
                method_local["constant_band"]["top1"] += int(constant_checks <= 1)
                method_local["constant_band"]["top3"] += int(constant_checks <= 3)
                method_local["constant_band"]["top5"] += int(constant_checks <= 5)
            else:
                constant_checks = ""
                constant_prediction = constant_ordered[0]
                constant_abs_error = abs(constant_prediction - p_n)
                method_local["constant_band"]["errors"].append(constant_abs_error)

            predicted_linear_offset = slope * test_index + intercept
            linear_interval_lo = int(round(seed - (predicted_linear_offset + linear_hi)))
            linear_interval_hi = int(round(seed - (predicted_linear_offset + linear_lo)))
            if linear_interval_hi < linear_interval_lo:
                linear_interval_lo, linear_interval_hi = linear_interval_hi, linear_interval_lo
            linear_primes = enumerate_primes(linear_interval_lo, linear_interval_hi)
            linear_target = seed - predicted_linear_offset
            linear_ordered = sorted(linear_primes, key=lambda value: (abs(value - linear_target), value))
            linear_contains = int(linear_interval_lo <= p_n <= linear_interval_hi)
            linear_width = linear_interval_hi - linear_interval_lo
            linear_prime_count = len(linear_primes)
            method_local["linear_band"]["widths"].append(linear_width)
            method_local["linear_band"]["prime_counts"].append(linear_prime_count)

            if not linear_primes:
                linear_checks = ""
                linear_prediction = ""
                linear_abs_error = ""
                method_local["linear_band"]["empty_intervals"] += 1
            elif linear_contains:
                linear_checks = linear_ordered.index(p_n) + 1
                linear_prediction = linear_ordered[0]
                linear_abs_error = abs(linear_prediction - p_n)
                method_local["linear_band"]["coverage"] += 1
                method_local["linear_band"]["checks"].append(linear_checks)
                method_local["linear_band"]["errors"].append(linear_abs_error)
                method_local["linear_band"]["top1"] += int(linear_checks <= 1)
                method_local["linear_band"]["top3"] += int(linear_checks <= 3)
                method_local["linear_band"]["top5"] += int(linear_checks <= 5)
            else:
                linear_checks = ""
                linear_prediction = linear_ordered[0]
                linear_abs_error = abs(linear_prediction - p_n)
                method_local["linear_band"]["errors"].append(linear_abs_error)

            rowwise_rows.extend(
                [
                    {
                        "dataset": row["dataset"],
                        "family": row["family"],
                        "decade_exponent": row["decade_exponent"],
                        "zone": row["zone"],
                        "n": row["n"],
                        "method": "constant_band",
                        "train_count": len(train_rows),
                        "test_count": len(test_rows),
                        "interval_lo": constant_interval_lo,
                        "interval_hi": constant_interval_hi,
                        "interval_width": constant_width,
                        "interval_prime_count": constant_prime_count,
                        "contains_true_prime": constant_contains,
                        "prediction": constant_prediction,
                        "abs_error": constant_abs_error,
                        "prime_checks": constant_checks,
                    },
                    {
                        "dataset": row["dataset"],
                        "family": row["family"],
                        "decade_exponent": row["decade_exponent"],
                        "zone": row["zone"],
                        "n": row["n"],
                        "method": "linear_band",
                        "train_count": len(train_rows),
                        "test_count": len(test_rows),
                        "interval_lo": linear_interval_lo,
                        "interval_hi": linear_interval_hi,
                        "interval_width": linear_width,
                        "interval_prime_count": linear_prime_count,
                        "contains_true_prime": linear_contains,
                        "prediction": linear_prediction,
                        "abs_error": linear_abs_error,
                        "prime_checks": linear_checks,
                    },
                ]
            )

        for method_name in ["constant_band", "linear_band"]:
            local = method_local[method_name]
            test_count = len(test_rows)
            coverage_rate = local["coverage"] / test_count
            class_rows.append(
                {
                    "method": method_name,
                    "decade_exponent": class_key[0],
                    "zone": class_key[1],
                    "train_count": len(train_rows),
                    "test_count": test_count,
                    "test_coverage_rate": f"{coverage_rate:.6f}",
                    "empty_interval_rate": f"{local['empty_intervals'] / test_count:.6f}",
                    "median_interval_width": int(np.median(np.array(local["widths"], dtype=float))),
                    "p90_interval_width": percentile(local["widths"], 90),
                    "median_interval_prime_count": int(np.median(np.array(local["prime_counts"], dtype=float))),
                    "p90_interval_prime_count": percentile(local["prime_counts"], 90),
                    "median_prime_checks_on_hits": int(np.median(np.array(local["checks"], dtype=float))) if local["checks"] else "",
                    "p90_prime_checks_on_hits": percentile(local["checks"], 90) if local["checks"] else "",
                }
            )

            per_method_coverages[method_name].extend([1] * local["coverage"] + [0] * (test_count - local["coverage"]))
            per_method_widths[method_name].extend(local["widths"])
            per_method_prime_counts[method_name].extend(local["prime_counts"])
            per_method_checks[method_name].extend(local["checks"])
            per_method_abs_error[method_name].extend(local["errors"])
            per_method_top1[method_name] += local["top1"]
            per_method_top3[method_name] += local["top3"]
            per_method_top5[method_name] += local["top5"]
            per_method_empty[method_name] += local["empty_intervals"]
            per_method_test_count[method_name] += test_count

    method_rows: list[dict[str, object]] = []
    for method_name in ["constant_band", "linear_band"]:
        test_count = per_method_test_count[method_name]
        checks = per_method_checks[method_name]
        widths = per_method_widths[method_name]
        prime_counts = per_method_prime_counts[method_name]
        errors = per_method_abs_error[method_name]
        method_rows.append(
            {
                "method": method_name,
                "test_row_count": test_count,
                "test_coverage_rate": f"{np.mean(np.array(per_method_coverages[method_name], dtype=float)):.6f}",
                "empty_interval_rate": f"{per_method_empty[method_name] / test_count:.6f}",
                "median_interval_width": int(np.median(np.array(widths, dtype=float))),
                "p90_interval_width": percentile(widths, 90),
                "max_interval_width": max(widths),
                "median_interval_prime_count": int(np.median(np.array(prime_counts, dtype=float))),
                "p90_interval_prime_count": percentile(prime_counts, 90),
                "max_interval_prime_count": max(prime_counts),
                "median_prime_checks_on_hits": int(np.median(np.array(checks, dtype=float))) if checks else "",
                "p90_prime_checks_on_hits": percentile(checks, 90) if checks else "",
                "max_prime_checks_on_hits": max(checks) if checks else "",
                "top1_rate": f"{per_method_top1[method_name] / test_count:.6f}",
                "top3_rate": f"{per_method_top3[method_name] / test_count:.6f}",
                "top5_rate": f"{per_method_top5[method_name] / test_count:.6f}",
                "median_abs_error": int(np.median(np.array(errors, dtype=float))) if errors else "",
                "p90_abs_error": percentile(errors, 90) if errors else "",
                "max_abs_error": max(errors) if errors else "",
            }
        )

    write_csv(
        OUTPUT_DIR / "rowwise_holdout_results.csv",
        [
            "dataset",
            "family",
            "decade_exponent",
            "zone",
            "n",
            "method",
            "train_count",
            "test_count",
            "interval_lo",
            "interval_hi",
            "interval_width",
            "interval_prime_count",
            "contains_true_prime",
            "prediction",
            "abs_error",
            "prime_checks",
        ],
        rowwise_rows,
    )
    write_csv(
        OUTPUT_DIR / "class_holdout_summary.csv",
        [
            "method",
            "decade_exponent",
            "zone",
            "train_count",
            "test_count",
            "test_coverage_rate",
            "empty_interval_rate",
            "median_interval_width",
            "p90_interval_width",
            "median_interval_prime_count",
            "p90_interval_prime_count",
            "median_prime_checks_on_hits",
            "p90_prime_checks_on_hits",
        ],
        class_rows,
    )
    write_csv(
        OUTPUT_DIR / "method_summary.csv",
        [
            "method",
            "test_row_count",
            "test_coverage_rate",
            "empty_interval_rate",
            "median_interval_width",
            "p90_interval_width",
            "max_interval_width",
            "median_interval_prime_count",
            "p90_interval_prime_count",
            "max_interval_prime_count",
            "median_prime_checks_on_hits",
            "p90_prime_checks_on_hits",
            "max_prime_checks_on_hits",
            "top1_rate",
            "top3_rate",
            "top5_rate",
            "median_abs_error",
            "p90_abs_error",
            "max_abs_error",
        ],
        method_rows,
    )

    plot_method_comparison(method_rows)
    plot_constant_coverage_by_class(class_rows)


if __name__ == "__main__":
    main()
