#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "benchmarks" / "gwr_hybrid_probe" / "rowwise_results.csv"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "gwr_local_locator"
PLOTS_DIR = OUTPUT_DIR / "plots"
PRIME_GAP_SRC = Path("/Users/velocityworks/IdeaProjects/prime-gap-structure/src/python")

if str(PRIME_GAP_SRC) not in sys.path:
    sys.path.insert(0, str(PRIME_GAP_SRC))

from z_band_prime_composite_field import divisor_counts_segment  # noqa: E402

TARGET_VARIANT = "r_inverse_seed"
TARGET_FAMILIES = {"boundary_window", "dense_local_window", "published_exact_grid"}

HEURISTIC_ORDER = [
    "nearest_d4",
    "edge_then_earliest",
    "edge_then_center",
    "edge2_then_center",
]

HEURISTIC_COLORS = {
    "nearest_d4": "#495057",
    "edge_then_earliest": "#1f77b4",
    "edge_then_center": "#0b7285",
    "edge2_then_center": "#c92a2a",
}


@dataclass(frozen=True)
class ProbeRow:
    dataset: str
    row_id: str
    family: str
    decade_exponent: int
    n: int
    p_n: int
    seed: int
    winner: int
    winner_divisor_count: int
    prime_minus_winner: int


def major_zone(n_value: int, decade_exponent: int) -> str:
    mantissa = n_value / (10**decade_exponent)
    if 0.49 <= mantissa <= 0.51:
        return "mant_0.5"
    if 0.89 <= mantissa <= 0.91:
        return "mant_0.9"
    if 0.999 <= mantissa <= 1.0011:
        return "mant_1.0"
    return "other"


def load_rows() -> list[ProbeRow]:
    dedup: dict[tuple[str, int], ProbeRow] = {}
    with INPUT_PATH.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["variant"] != TARGET_VARIANT:
                continue
            if row["family"] not in TARGET_FAMILIES:
                continue
            probe_row = ProbeRow(
                dataset=row["dataset"],
                row_id=row["row_id"],
                family=row["family"],
                decade_exponent=int(row["decade_exponent"]),
                n=int(row["n"]),
                p_n=int(row["p_n"]),
                seed=int(row["seed"]),
                winner=int(row["winner"]),
                winner_divisor_count=int(row["winner_divisor_count"]),
                prime_minus_winner=int(row["prime_minus_winner"]),
            )
            dedup[(probe_row.dataset, probe_row.n)] = probe_row
    return sorted(dedup.values(), key=lambda row: row.p_n)


def percentile(values: list[int], pct: float) -> int:
    if not values:
        raise ValueError("values must be non-empty")
    return int(np.percentile(np.array(values, dtype=float), pct))


def split_prime_runs(sorted_primes: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    current: list[int] = []
    previous_prime: int | None = None
    for prime_value in sorted_primes:
        if previous_prime is None:
            current = [prime_value]
        elif int(gp.prev_prime(prime_value)) == previous_prime:
            current.append(prime_value)
        else:
            runs.append(current)
            current = [prime_value]
        previous_prime = prime_value
    if current:
        runs.append(current)
    return runs


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def choose_nearest_d4(candidates: list[int], center: int, _: dict[int, int]) -> int:
    return min(candidates, key=lambda value: (abs(value - center), value))


def choose_edge_then_earliest(candidates: list[int], _: int, left_distance: dict[int, int]) -> int:
    return min(candidates, key=lambda value: (left_distance[value], value))


def choose_edge_then_center(candidates: list[int], center: int, left_distance: dict[int, int]) -> int:
    return min(candidates, key=lambda value: (left_distance[value], abs(value - center), value))


def choose_edge2_then_center(candidates: list[int], center: int, left_distance: dict[int, int]) -> int:
    edge2 = [value for value in candidates if left_distance[value] == 2]
    if edge2:
        return min(edge2, key=lambda value: (abs(value - center), value))
    min_left = min(left_distance[value] for value in candidates)
    pool = [value for value in candidates if left_distance[value] == min_left]
    return min(pool, key=lambda value: (abs(value - center), value))


HEURISTICS = {
    "nearest_d4": choose_nearest_d4,
    "edge_then_earliest": choose_edge_then_earliest,
    "edge_then_center": choose_edge_then_center,
    "edge2_then_center": choose_edge2_then_center,
}


def plot_heuristic_rates(summary_rows: list[dict[str, object]]) -> None:
    labels = [row["heuristic"] for row in summary_rows]
    witness_all = [float(row["witness_match_rate_all"]) for row in summary_rows]
    witness_d4 = [float(row["witness_match_rate_d4_truth"]) for row in summary_rows]
    prime_all = [float(row["prime_match_rate_all"]) for row in summary_rows]
    prime_d4 = [float(row["prime_match_rate_d4_truth"]) for row in summary_rows]

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8))
    x = np.arange(len(labels))
    width = 0.36

    axes[0].bar(x - width / 2, witness_all, width=width, color="#74c0fc", label="all rows")
    axes[0].bar(x + width / 2, witness_d4, width=width, color="#0b7285", label="d=4 truth rows")
    axes[0].set_title("Exact witness recovery")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=25, ha="right")
    axes[0].set_ylim(0.0, 1.0)
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend()

    axes[1].bar(x - width / 2, prime_all, width=width, color="#ffa94d", label="all rows")
    axes[1].bar(x + width / 2, prime_d4, width=width, color="#c92a2a", label="d=4 truth rows")
    axes[1].set_title("Exact prime recovery via nextprime(candidate)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=25, ha="right")
    axes[1].set_ylim(0.0, 1.0)
    axes[1].grid(axis="y", alpha=0.25)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "heuristic_match_rates.png", dpi=200)
    plt.close(fig)


def plot_best_by_decade(decade_rows: list[dict[str, object]], best_heuristic: str) -> None:
    rows = [row for row in decade_rows if row["heuristic"] == best_heuristic]
    xs = np.array([int(row["decade_exponent"]) for row in rows], dtype=float)
    witness_rate = np.array([float(row["witness_match_rate_d4_truth"]) for row in rows], dtype=float)
    prime_rate = np.array([float(row["prime_match_rate_d4_truth"]) for row in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.plot(xs, witness_rate, marker="o", linewidth=2, color="#0b7285", label="witness match on d=4 truth rows")
    ax.plot(xs, prime_rate, marker="o", linewidth=2, color="#c92a2a", label="prime match on d=4 truth rows")
    ax.set_ylim(0.0, 1.0)
    ax.set_xlabel("Decade exponent of n")
    ax.set_ylabel("Match rate")
    ax.set_title(f"{best_heuristic} by exact decade")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "best_heuristic_by_decade.png", dpi=200)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_rows()

    offsets_by_class: dict[tuple[int, str], list[int]] = defaultdict(list)
    for row in rows:
        offsets_by_class[(row.decade_exponent, major_zone(row.n, row.decade_exponent))].append(row.seed - row.winner)

    class_center: dict[tuple[int, str], int] = {}
    class_radius: dict[tuple[int, str], int] = {}
    bracket_rows: list[dict[str, object]] = []
    for key in sorted(offsets_by_class):
        values = sorted(offsets_by_class[key])
        center = int(np.median(np.array(values, dtype=float)))
        radius = max(abs(value - center) for value in values)
        class_center[key] = center
        class_radius[key] = radius
        bracket_rows.append(
            {
                "decade_exponent": key[0],
                "zone": key[1],
                "row_count": len(values),
                "center_offset": center,
                "radius": radius,
                "min_offset": values[0],
                "max_offset": values[-1],
            }
        )

    prime_to_row = {row.p_n: row for row in rows}
    runs = split_prime_runs(sorted(prime_to_row))
    prev_prime_cache: dict[int, int] = {}
    next_prime_cache: dict[int, int] = {}

    result_rows: list[dict[str, object]] = []

    for run in runs:
        run_rows = [prime_to_row[prime_value] for prime_value in run]
        local_bounds = []
        for row in run_rows:
            class_key = (row.decade_exponent, major_zone(row.n, row.decade_exponent))
            center = row.seed - class_center[class_key]
            radius = class_radius[class_key]
            local_bounds.append((center - radius, center + radius))

        window_lo = min(bound[0] for bound in local_bounds)
        window_hi = max(bound[1] for bound in local_bounds) + 1
        divisor_counts = divisor_counts_segment(window_lo, window_hi)

        d4_values = [
            window_lo + index
            for index, divisor_count in enumerate(divisor_counts)
            if int(divisor_count) == 4
        ]

        for row in run_rows:
            class_key = (row.decade_exponent, major_zone(row.n, row.decade_exponent))
            center_offset = class_center[class_key]
            radius = class_radius[class_key]
            center = row.seed - center_offset
            left = center - radius
            right = center + radius
            bracket_candidates = [value for value in d4_values if left <= value <= right]
            left_distance = {}
            for value in bracket_candidates:
                cached_prev = prev_prime_cache.get(value)
                if cached_prev is None:
                    cached_prev = int(gp.prev_prime(value))
                    prev_prime_cache[value] = cached_prev
                left_distance[value] = value - cached_prev

            for heuristic_name in HEURISTIC_ORDER:
                candidate = HEURISTICS[heuristic_name](bracket_candidates, center, left_distance)
                cached_next = next_prime_cache.get(candidate)
                if cached_next is None:
                    cached_next = int(gp.next_prime(candidate))
                    next_prime_cache[candidate] = cached_next
                result_rows.append(
                    {
                        "heuristic": heuristic_name,
                        "dataset": row.dataset,
                        "family": row.family,
                        "decade_exponent": row.decade_exponent,
                        "zone": class_key[1],
                        "n": row.n,
                        "p_n": row.p_n,
                        "seed": row.seed,
                        "predicted_center": center,
                        "center_offset": center_offset,
                        "radius": radius,
                        "winner": row.winner,
                        "winner_divisor_count": row.winner_divisor_count,
                        "candidate": candidate,
                        "candidate_minus_winner": candidate - row.winner,
                        "abs_candidate_minus_winner": abs(candidate - row.winner),
                        "candidate_left_edge_distance": left_distance[candidate],
                        "predicted_prime": cached_next,
                        "predicted_prime_minus_true": cached_next - row.p_n,
                        "abs_predicted_prime_minus_true": abs(cached_next - row.p_n),
                        "witness_match": int(candidate == row.winner),
                        "prime_match": int(cached_next == row.p_n),
                        "bracket_candidate_count": len(bracket_candidates),
                    }
                )

    summary_rows: list[dict[str, object]] = []
    decade_rows: list[dict[str, object]] = []
    for heuristic_name in HEURISTIC_ORDER:
        subset = [row for row in result_rows if row["heuristic"] == heuristic_name]
        d4_truth = [row for row in subset if row["winner_divisor_count"] == 4]
        summary_rows.append(
            {
                "heuristic": heuristic_name,
                "row_count": len(subset),
                "d4_truth_row_count": len(d4_truth),
                "witness_match_rate_all": f"{np.mean([row['witness_match'] for row in subset]):.6f}",
                "witness_match_rate_d4_truth": f"{np.mean([row['witness_match'] for row in d4_truth]):.6f}",
                "prime_match_rate_all": f"{np.mean([row['prime_match'] for row in subset]):.6f}",
                "prime_match_rate_d4_truth": f"{np.mean([row['prime_match'] for row in d4_truth]):.6f}",
                "median_abs_candidate_minus_winner": f"{np.median([row['abs_candidate_minus_winner'] for row in subset]):.3f}",
                "p90_abs_candidate_minus_winner": f"{percentile([int(row['abs_candidate_minus_winner']) for row in subset], 90):.3f}",
                "median_abs_predicted_prime_minus_true": f"{np.median([row['abs_predicted_prime_minus_true'] for row in subset]):.3f}",
                "p90_abs_predicted_prime_minus_true": f"{percentile([int(row['abs_predicted_prime_minus_true']) for row in subset], 90):.3f}",
                "median_bracket_candidate_count": f"{np.median([row['bracket_candidate_count'] for row in subset]):.3f}",
            }
        )
        for decade_exponent in sorted({int(row["decade_exponent"]) for row in subset}):
            decade_subset = [row for row in subset if int(row["decade_exponent"]) == decade_exponent]
            decade_d4 = [row for row in decade_subset if row["winner_divisor_count"] == 4]
            decade_rows.append(
                {
                    "heuristic": heuristic_name,
                    "decade_exponent": decade_exponent,
                    "row_count": len(decade_subset),
                    "d4_truth_row_count": len(decade_d4),
                    "witness_match_rate_all": f"{np.mean([row['witness_match'] for row in decade_subset]):.6f}",
                    "witness_match_rate_d4_truth": f"{np.mean([row['witness_match'] for row in decade_d4]):.6f}",
                    "prime_match_rate_all": f"{np.mean([row['prime_match'] for row in decade_subset]):.6f}",
                    "prime_match_rate_d4_truth": f"{np.mean([row['prime_match'] for row in decade_d4]):.6f}",
                }
            )

    best_heuristic = max(summary_rows, key=lambda row: float(row["prime_match_rate_d4_truth"]))["heuristic"]

    write_csv(
        OUTPUT_DIR / "class_brackets.csv",
        ["decade_exponent", "zone", "row_count", "center_offset", "radius", "min_offset", "max_offset"],
        bracket_rows,
    )
    write_csv(
        OUTPUT_DIR / "rowwise_locator_results.csv",
        [
            "heuristic",
            "dataset",
            "family",
            "decade_exponent",
            "zone",
            "n",
            "p_n",
            "seed",
            "predicted_center",
            "center_offset",
            "radius",
            "winner",
            "winner_divisor_count",
            "candidate",
            "candidate_minus_winner",
            "abs_candidate_minus_winner",
            "candidate_left_edge_distance",
            "predicted_prime",
            "predicted_prime_minus_true",
            "abs_predicted_prime_minus_true",
            "witness_match",
            "prime_match",
            "bracket_candidate_count",
        ],
        result_rows,
    )
    write_csv(
        OUTPUT_DIR / "heuristic_summary.csv",
        [
            "heuristic",
            "row_count",
            "d4_truth_row_count",
            "witness_match_rate_all",
            "witness_match_rate_d4_truth",
            "prime_match_rate_all",
            "prime_match_rate_d4_truth",
            "median_abs_candidate_minus_winner",
            "p90_abs_candidate_minus_winner",
            "median_abs_predicted_prime_minus_true",
            "p90_abs_predicted_prime_minus_true",
            "median_bracket_candidate_count",
        ],
        summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "heuristic_by_decade.csv",
        [
            "heuristic",
            "decade_exponent",
            "row_count",
            "d4_truth_row_count",
            "witness_match_rate_all",
            "witness_match_rate_d4_truth",
            "prime_match_rate_all",
            "prime_match_rate_d4_truth",
        ],
        decade_rows,
    )

    plot_heuristic_rates(summary_rows)
    plot_best_by_decade(decade_rows, best_heuristic)


if __name__ == "__main__":
    main()
