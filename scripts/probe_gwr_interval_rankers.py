#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "benchmarks" / "gwr_hybrid_probe" / "rowwise_results.csv"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "gwr_interval_rankers"
PLOTS_DIR = OUTPUT_DIR / "plots"

TARGET_VARIANT = "r_inverse_seed"
TARGET_FAMILIES = {"boundary_window", "dense_local_window", "published_exact_grid"}
TOP_K_VALUES = [1, 3, 5]


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


def order_nearest(primes: list[int], target: float) -> list[int]:
    return sorted(primes, key=lambda value: (abs(value - target), value))


def order_from_target(primes: list[int], target: float) -> list[int]:
    right = [value for value in primes if value >= target]
    left = [value for value in primes if value < target]
    return right + list(reversed(left))


def plot_prime_checks(summary_rows: list[dict[str, object]]) -> None:
    labels = [row["method"] for row in summary_rows]
    medians = [int(row["median_prime_checks"]) for row in summary_rows]
    p90s = [int(row["p90_prime_checks"]) for row in summary_rows]
    maximums = [int(row["max_prime_checks"]) for row in summary_rows]

    fig, ax = plt.subplots(figsize=(11.0, 5.2))
    x = np.arange(len(labels))
    width = 0.26
    ax.bar(x - width, medians, width=width, color="#0b7285", label="median")
    ax.bar(x, p90s, width=width, color="#74c0fc", label="p90")
    ax.bar(x + width, maximums, width=width, color="#c92a2a", label="max")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Prime checks until the true prime is found")
    ax.set_title("Search cost inside the trapped interval")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "prime_checks_by_method.png", dpi=200)
    plt.close(fig)


def plot_topk(summary_rows: list[dict[str, object]]) -> None:
    labels = [row["method"] for row in summary_rows]
    top1 = [float(row["top1_rate"]) for row in summary_rows]
    top3 = [float(row["top3_rate"]) for row in summary_rows]
    top5 = [float(row["top5_rate"]) for row in summary_rows]

    fig, ax = plt.subplots(figsize=(11.0, 5.2))
    x = np.arange(len(labels))
    width = 0.24
    ax.bar(x - width, top1, width=width, color="#495057", label="top1")
    ax.bar(x, top3, width=width, color="#0b7285", label="top3")
    ax.bar(x + width, top5, width=width, color="#74c0fc", label="top5")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Exact coverage rate")
    ax.set_title("How often the true prime is among the first few ranked candidates")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "topk_coverage_by_method.png", dpi=200)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    unique_rows: list[dict[str, int | str]] = []
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

    grouped_offsets: dict[tuple[int, str], list[int]] = defaultdict(list)
    grouped_tails: dict[tuple[int, str], list[int]] = defaultdict(list)
    grouped_prime_offsets: dict[tuple[int, str], list[int]] = defaultdict(list)
    for row in unique_rows:
        class_key = (int(row["decade_exponent"]), major_zone(int(row["n"]), int(row["decade_exponent"])))
        seed_minus_winner = int(row["seed_minus_winner"])
        prime_minus_winner = int(row["prime_minus_winner"])
        grouped_offsets[class_key].append(seed_minus_winner)
        grouped_tails[class_key].append(prime_minus_winner)
        grouped_prime_offsets[class_key].append(seed_minus_winner - prime_minus_winner)

    class_rows: list[dict[str, object]] = []
    class_stats: dict[tuple[int, str], dict[str, int]] = {}
    for class_key in sorted(grouped_offsets):
        offsets = sorted(grouped_offsets[class_key])
        tails = sorted(grouped_tails[class_key])
        prime_offsets = sorted(grouped_prime_offsets[class_key])
        stats = {
            "min_offset": offsets[0],
            "max_offset": offsets[-1],
            "median_witness_offset": int(np.median(np.array(offsets, dtype=float))),
            "median_tail": int(np.median(np.array(tails, dtype=float))),
            "tail_max": tails[-1],
            "median_prime_offset": int(np.median(np.array(prime_offsets, dtype=float))),
        }
        class_stats[class_key] = stats
        class_rows.append(
            {
                "decade_exponent": class_key[0],
                "zone": class_key[1],
                "row_count": len(offsets),
                "min_offset": stats["min_offset"],
                "max_offset": stats["max_offset"],
                "median_witness_offset": stats["median_witness_offset"],
                "median_tail": stats["median_tail"],
                "tail_max": stats["tail_max"],
                "median_prime_offset": stats["median_prime_offset"],
            }
        )

    method_orders = {
        "ascending_lo": lambda primes, targets: primes,
        "nearest_seed": lambda primes, targets: order_nearest(primes, targets["seed"]),
        "nearest_interval_mid": lambda primes, targets: order_nearest(primes, targets["interval_mid"]),
        "nearest_prime_center": lambda primes, targets: order_nearest(primes, targets["prime_center"]),
        "from_prime_center": lambda primes, targets: order_from_target(primes, targets["prime_center"]),
        "nearest_witness_tail_center": lambda primes, targets: order_nearest(primes, targets["witness_tail_center"]),
        "from_witness_tail_center": lambda primes, targets: order_from_target(primes, targets["witness_tail_center"]),
    }

    method_rows: list[dict[str, object]] = []
    rowwise_rows: list[dict[str, object]] = []
    per_method_checks: dict[str, list[int]] = defaultdict(list)
    per_method_errors: dict[str, list[int]] = defaultdict(list)
    per_method_prime_counts: dict[str, list[int]] = defaultdict(list)
    per_method_top_hits: dict[str, dict[int, int]] = {
        method: {k_value: 0 for k_value in TOP_K_VALUES} for method in method_orders
    }

    for row in unique_rows:
        class_key = (int(row["decade_exponent"]), major_zone(int(row["n"]), int(row["decade_exponent"])))
        stats = class_stats[class_key]
        seed = int(row["seed"])
        p_n = int(row["p_n"])
        interval_lo = seed - int(stats["max_offset"])
        interval_hi = seed - int(stats["min_offset"]) + int(stats["tail_max"])
        interval_mid = (interval_lo + interval_hi) / 2.0
        prime_center = seed - int(stats["median_prime_offset"])
        witness_tail_center = seed - int(stats["median_witness_offset"]) + int(stats["median_tail"])
        primes = enumerate_primes(interval_lo, interval_hi)
        prime_count = len(primes)
        if not primes:
            raise RuntimeError(f"no primes found in interval [{interval_lo}, {interval_hi}]")

        targets = {
            "seed": float(seed),
            "interval_mid": interval_mid,
            "prime_center": float(prime_center),
            "witness_tail_center": float(witness_tail_center),
        }

        for method_name, order_fn in method_orders.items():
            ordered = order_fn(primes, targets)
            prime_checks = ordered.index(p_n) + 1
            prediction = ordered[0]
            abs_error = abs(prediction - p_n)

            per_method_checks[method_name].append(prime_checks)
            per_method_errors[method_name].append(abs_error)
            per_method_prime_counts[method_name].append(prime_count)
            for k_value in TOP_K_VALUES:
                if prime_checks <= k_value:
                    per_method_top_hits[method_name][k_value] += 1

            rowwise_rows.append(
                {
                    "dataset": row["dataset"],
                    "family": row["family"],
                    "decade_exponent": row["decade_exponent"],
                    "zone": class_key[1],
                    "n": row["n"],
                    "p_n": p_n,
                    "method": method_name,
                    "interval_lo": interval_lo,
                    "interval_hi": interval_hi,
                    "interval_prime_count": prime_count,
                    "seed": seed,
                    "prime_center": int(prime_center),
                    "witness_tail_center": int(witness_tail_center),
                    "prediction": prediction,
                    "abs_error": abs_error,
                    "prime_checks": prime_checks,
                    "top1_hit": int(prime_checks <= 1),
                    "top3_hit": int(prime_checks <= 3),
                    "top5_hit": int(prime_checks <= 5),
                }
            )

    row_count = len(unique_rows)
    for method_name in method_orders:
        checks = per_method_checks[method_name]
        errors = per_method_errors[method_name]
        prime_counts = per_method_prime_counts[method_name]
        method_rows.append(
            {
                "method": method_name,
                "row_count": row_count,
                "median_interval_prime_count": int(np.median(np.array(prime_counts, dtype=float))),
                "p90_interval_prime_count": percentile(prime_counts, 90),
                "median_prime_checks": int(np.median(np.array(checks, dtype=float))),
                "p90_prime_checks": percentile(checks, 90),
                "max_prime_checks": max(checks),
                "top1_rate": f"{per_method_top_hits[method_name][1] / row_count:.6f}",
                "top3_rate": f"{per_method_top_hits[method_name][3] / row_count:.6f}",
                "top5_rate": f"{per_method_top_hits[method_name][5] / row_count:.6f}",
                "median_abs_error": int(np.median(np.array(errors, dtype=float))),
                "p90_abs_error": percentile(errors, 90),
                "max_abs_error": max(errors),
            }
        )

    write_csv(
        OUTPUT_DIR / "class_target_summary.csv",
        [
            "decade_exponent",
            "zone",
            "row_count",
            "min_offset",
            "max_offset",
            "median_witness_offset",
            "median_tail",
            "tail_max",
            "median_prime_offset",
        ],
        class_rows,
    )
    write_csv(
        OUTPUT_DIR / "rowwise_rank_results.csv",
        [
            "dataset",
            "family",
            "decade_exponent",
            "zone",
            "n",
            "p_n",
            "method",
            "interval_lo",
            "interval_hi",
            "interval_prime_count",
            "seed",
            "prime_center",
            "witness_tail_center",
            "prediction",
            "abs_error",
            "prime_checks",
            "top1_hit",
            "top3_hit",
            "top5_hit",
        ],
        rowwise_rows,
    )
    write_csv(
        OUTPUT_DIR / "method_summary.csv",
        [
            "method",
            "row_count",
            "median_interval_prime_count",
            "p90_interval_prime_count",
            "median_prime_checks",
            "p90_prime_checks",
            "max_prime_checks",
            "top1_rate",
            "top3_rate",
            "top5_rate",
            "median_abs_error",
            "p90_abs_error",
            "max_abs_error",
        ],
        method_rows,
    )

    plot_prime_checks(method_rows)
    plot_topk(method_rows)


if __name__ == "__main__":
    main()
