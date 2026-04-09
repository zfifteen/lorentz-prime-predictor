#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np
from sympy import mobius


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "gwr_hybrid_probe"
PLOTS_DIR = OUTPUT_DIR / "plots"
PYTHON_SRC = REPO_ROOT / "src" / "python"
PRIME_GAP_SRC = Path("/Users/velocityworks/IdeaProjects/prime-gap-structure/src/python")

if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))
if str(PRIME_GAP_SRC) not in sys.path:
    sys.path.insert(0, str(PRIME_GAP_SRC))

from lpp.predictor import lpp_seed  # noqa: E402
from z_band_prime_composite_field import divisor_counts_segment  # noqa: E402


DATASETS = [
    ("reproducible_exact_baseline", DATA_DIR / "held_out_exact_primes_1e4_1e12.csv"),
    ("reproducible_exact_stage_a", DATA_DIR / "held_out_exact_primes_1e13_1e14.csv"),
    ("reproducible_exact_stage_b", DATA_DIR / "held_out_exact_primes_1e15_1e16.csv"),
]

DATASET_LABELS = {
    "reproducible_exact_baseline": "baseline",
    "reproducible_exact_stage_a": "stage_a",
    "reproducible_exact_stage_b": "stage_b",
}

VARIANT_ORDER = [
    "lpp_seed",
    "cipolla_log5_repacked",
    "r_inverse_seed",
]

VARIANT_COLORS = {
    "lpp_seed": "#1f77b4",
    "cipolla_log5_repacked": "#0b7285",
    "r_inverse_seed": "#c92a2a",
}

CIPOLLA_RAW_POLYNOMIALS = {
    3: [-131, 84, -21, 2],
    4: [2666, -1908, 588, -92, 6],
    5: [-81534, 62860, -22020, 4380, -490, 24],
}

RADIUS_GRID = [
    64,
    256,
    1024,
    4096,
    16384,
    65536,
    262144,
    1048576,
    4194304,
    16777216,
]


@dataclass(frozen=True)
class DatasetRow:
    dataset: str
    row_id: str
    family: str
    decade_exponent: int
    n: int
    p_n: int


@dataclass(frozen=True)
class GapWitness:
    p_prev: int
    p_n: int
    gap: int
    winner: int
    winner_divisor_count: int
    prime_minus_winner: int
    composite_threat: int | None
    composite_threat_minus_winner: int | None


def load_rows() -> list[DatasetRow]:
    rows: list[DatasetRow] = []
    for dataset_name, path in DATASETS:
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(
                    DatasetRow(
                        dataset=dataset_name,
                        row_id=row["row_id"],
                        family=row["family"],
                        decade_exponent=int(row["decade_exponent"]),
                        n=int(row["n"]),
                        p_n=int(row["p_n"]),
                    )
                )
    return rows


def compute_basis(unique_n_values: list[int]) -> dict[int, dict[str, float]]:
    basis: dict[int, dict[str, float]] = {}
    for n_value in unique_n_values:
        precision = max(256, int(gp.log2(n_value)) + 256)
        with gp.context(gp.get_context(), precision=precision):
            n_mp = gp.mpfr(n_value)
            ln_n = gp.log(n_mp)
            ln_ln_n = gp.log(ln_n)
            pnt = n_mp * (ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n))
            if pnt <= 0:
                pnt = n_mp
            ln_p = gp.log(pnt)
            basis[n_value] = {
                "P": float(pnt),
                "L": float(ln_n),
                "LL": float(ln_ln_n),
                "LP": float(ln_p),
                "B": float(pnt / n_mp),
            }
    return basis


def c_n_value(basis_row: dict[str, float]) -> float:
    ln_n = basis_row["L"]
    ln_ln_n = basis_row["LL"]
    ln_p = basis_row["LP"]
    backbone_ratio = basis_row["B"]
    poly2 = (ln_ln_n**2) - 6.0 * ln_ln_n + 11.0
    return -poly2 / (2.0 * (ln_n**2) * backbone_ratio * ((ln_p / (math.e**4)) ** 2))


def cipolla_polynomial(order: int, ln_ln_n: float) -> float:
    coefficients = CIPOLLA_RAW_POLYNOMIALS[order]
    total = 0.0
    for power, coefficient in enumerate(coefficients):
        total += coefficient * (ln_ln_n**power)
    return total / math.factorial(order)


def repacked_kappa_order5(basis_row: dict[str, float]) -> float:
    pnt = basis_row["P"]
    ln_n = basis_row["L"]
    ln_ln_n = basis_row["LL"]
    n_value = pnt / basis_row["B"]
    residual = 0.0
    for order in range(3, 6):
        sign = 1.0 if order % 2 == 1 else -1.0
        residual += n_value * sign * cipolla_polynomial(order, ln_ln_n) / (ln_n**order)
    return residual / (pnt ** (2.0 / 3.0))


def cipolla_log5_repacked_seed(n_value: int, basis_row: dict[str, float]) -> int:
    pnt = basis_row["P"]
    ln_p = basis_row["LP"]
    d_value = c_n_value(basis_row) * pnt * ((ln_p / (math.e**4)) ** 2)
    kappa = repacked_kappa_order5(basis_row)
    estimate = pnt + d_value + kappa * (pnt ** (2.0 / 3.0))
    return math.floor(estimate + 0.5)


def riemann_r(x_value: mp.mpf, truncation_k: int) -> mp.mpf:
    total = mp.mpf("0")
    for k_value in range(1, truncation_k + 1):
        mu_value = mobius(k_value)
        if mu_value == 0:
            continue
        total += mp.mpf(mu_value) / k_value * mp.li(x_value ** (mp.mpf(1) / k_value))
    return total


def riemann_r_derivative(x_value: mp.mpf, truncation_k: int) -> mp.mpf:
    total = mp.mpf("0")
    for k_value in range(1, truncation_k + 1):
        mu_value = mobius(k_value)
        if mu_value == 0:
            continue
        total += mp.mpf(mu_value) / k_value * (x_value ** (mp.mpf(1) / k_value - 1))
    return total / mp.log(x_value)


def r_inverse_seed(n_value: int, basis_row: dict[str, float], truncation_k: int = 8, newton_steps: int = 2) -> int:
    mp.mp.dps = 100
    x_value = mp.mpf(cipolla_log5_repacked_seed(n_value, basis_row))
    target = mp.mpf(n_value)
    for _ in range(newton_steps):
        x_value -= (riemann_r(x_value, truncation_k) - target) / riemann_r_derivative(x_value, truncation_k)
    return int(gp.mpz(x_value + 0.5))


def estimate_variant(variant_name: str, n_value: int, basis_row: dict[str, float]) -> int:
    if variant_name == "lpp_seed":
        return lpp_seed(n_value)
    if variant_name == "cipolla_log5_repacked":
        return cipolla_log5_repacked_seed(n_value, basis_row)
    if variant_name == "r_inverse_seed":
        return r_inverse_seed(n_value, basis_row)
    raise ValueError(f"unknown variant: {variant_name}")


def next_prime_square_after(value: int) -> int:
    root = gp.isqrt(value)
    return int(gp.next_prime(root) ** 2)


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


def compute_gap_witness_cache(rows: list[DatasetRow]) -> dict[int, GapWitness]:
    unique_primes = sorted({row.p_n for row in rows})
    runs = split_prime_runs(unique_primes)
    cache: dict[int, GapWitness] = {}
    for run in runs:
        first_prime = run[0]
        left_prime = int(gp.prev_prime(first_prime))
        right_prime = run[-1]
        divisor_count = divisor_counts_segment(left_prime + 1, right_prime)
        lo = left_prime + 1
        previous = left_prime
        for prime_value in run:
            start = previous + 1 - lo
            stop = prime_value - lo
            gap_divisors = divisor_count[start:stop]
            winner_divisor_count = int(np.min(gap_divisors))
            winner_index = int(np.flatnonzero(gap_divisors == winner_divisor_count)[0])
            winner = previous + 1 + winner_index
            composite_threat = None
            if winner_divisor_count == 4:
                composite_threat = next_prime_square_after(winner)
            cache[prime_value] = GapWitness(
                p_prev=previous,
                p_n=prime_value,
                gap=prime_value - previous,
                winner=winner,
                winner_divisor_count=winner_divisor_count,
                prime_minus_winner=prime_value - winner,
                composite_threat=composite_threat,
                composite_threat_minus_winner=None if composite_threat is None else composite_threat - winner,
            )
            previous = prime_value
    return cache


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return math.nan
    return float(np.percentile(np.array(values, dtype=float), pct))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_variant_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for variant_name in VARIANT_ORDER:
        variant_rows = [row for row in rows if row["variant"] == variant_name]
        abs_prime = [float(row["abs_seed_minus_prime"]) for row in variant_rows]
        abs_witness = [float(row["abs_seed_minus_winner"]) for row in variant_rows]
        gain = [float(row["witness_target_gain"]) for row in variant_rows]
        d4_rows = [row for row in variant_rows if row["winner_divisor_count"] == 4]
        d4_prime_tail = [float(row["prime_minus_winner"]) for row in d4_rows]
        d4_closure = [float(row["composite_threat_minus_winner"]) for row in d4_rows if row["composite_threat_minus_winner"] != ""]
        summary.append(
            {
                "variant": variant_name,
                "row_count": len(variant_rows),
                "d4_row_count": len(d4_rows),
                "median_abs_seed_minus_prime": f"{np.median(abs_prime):.3f}",
                "median_abs_seed_minus_winner": f"{np.median(abs_witness):.3f}",
                "median_witness_target_gain": f"{np.median(gain):.3f}",
                "p90_abs_seed_minus_winner": f"{percentile(abs_witness, 90):.3f}",
                "max_abs_seed_minus_winner": f"{max(abs_witness):.3f}",
                "coverage_le_4096": f"{sum(value <= 4096 for value in abs_witness) / len(abs_witness):.6f}",
                "coverage_le_65536": f"{sum(value <= 65536 for value in abs_witness) / len(abs_witness):.6f}",
                "coverage_le_1048576": f"{sum(value <= 1048576 for value in abs_witness) / len(abs_witness):.6f}",
                "median_prime_minus_winner_d4": f"{np.median(d4_prime_tail):.3f}",
                "median_composite_threat_minus_winner_d4": f"{np.median(d4_closure):.3f}",
            }
        )
    return summary


def build_dataset_variant_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for dataset_name, _ in DATASETS:
        for variant_name in VARIANT_ORDER:
            subset = [row for row in rows if row["dataset"] == dataset_name and row["variant"] == variant_name]
            abs_witness = [float(row["abs_seed_minus_winner"]) for row in subset]
            gain = [float(row["witness_target_gain"]) for row in subset]
            summary.append(
                {
                    "dataset": dataset_name,
                    "variant": variant_name,
                    "row_count": len(subset),
                    "median_abs_seed_minus_winner": f"{np.median(abs_witness):.3f}",
                    "p90_abs_seed_minus_winner": f"{percentile(abs_witness, 90):.3f}",
                    "coverage_le_65536": f"{sum(value <= 65536 for value in abs_witness) / len(abs_witness):.6f}",
                    "coverage_le_1048576": f"{sum(value <= 1048576 for value in abs_witness) / len(abs_witness):.6f}",
                    "median_witness_target_gain": f"{np.median(gain):.3f}",
                }
            )
    return summary


def build_witness_summary(cache: dict[int, GapWitness]) -> list[dict[str, object]]:
    witnesses = list(cache.values())
    d4_rows = [row for row in witnesses if row.winner_divisor_count == 4 and row.composite_threat_minus_winner is not None]
    return [
        {
            "prime_count": len(witnesses),
            "d4_share": f"{len(d4_rows) / len(witnesses):.6f}",
            "median_gap": f"{np.median([row.gap for row in witnesses]):.3f}",
            "median_prime_minus_winner": f"{np.median([row.prime_minus_winner for row in witnesses]):.3f}",
            "p90_prime_minus_winner": f"{percentile([row.prime_minus_winner for row in witnesses], 90):.3f}",
            "median_composite_threat_minus_winner_d4": f"{np.median([row.composite_threat_minus_winner for row in d4_rows]):.3f}",
            "p10_prime_position_inside_d4_closure": (
                f"{percentile([row.prime_minus_winner / row.composite_threat_minus_winner for row in d4_rows], 10):.6f}"
            ),
            "median_prime_position_inside_d4_closure": (
                f"{np.median([row.prime_minus_winner / row.composite_threat_minus_winner for row in d4_rows]):.6f}"
            ),
        }
    ]


def plot_radius_coverage(rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    for variant_name in VARIANT_ORDER:
        subset = [row for row in rows if row["variant"] == variant_name]
        abs_witness = np.array([float(row["abs_seed_minus_winner"]) for row in subset], dtype=float)
        coverage = [float(np.mean(abs_witness <= radius)) for radius in RADIUS_GRID]
        ax.plot(RADIUS_GRID, coverage, marker="o", linewidth=2, color=VARIANT_COLORS[variant_name], label=variant_name)
    ax.set_xscale("log", base=2)
    ax.set_ylim(0.0, 1.02)
    ax.set_xlabel("Search radius around seed")
    ax.set_ylabel("Exact rows with witness inside radius")
    ax.set_title("How close each seed lands to the true preceding-gap GWR witness")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "witness_radius_coverage.png", dpi=200)
    plt.close(fig)


def plot_prime_vs_closure(cache: dict[int, GapWitness]) -> None:
    d4_rows = [row for row in cache.values() if row.winner_divisor_count == 4 and row.composite_threat_minus_winner is not None]
    prime_tail = np.array([row.prime_minus_winner for row in d4_rows], dtype=float)
    closure_tail = np.array([row.composite_threat_minus_winner for row in d4_rows], dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8))

    axes[0].hist(prime_tail, bins=40, color="#0b7285", alpha=0.85)
    axes[0].set_title("True search after the witness")
    axes[0].set_xlabel("q - w")
    axes[0].set_ylabel("Count")
    axes[0].grid(alpha=0.2)

    axes[1].hist(closure_tail, bins=40, color="#c92a2a", alpha=0.85)
    axes[1].set_title("Composite-threat ceiling in d=4 gaps")
    axes[1].set_xlabel("T_comp(w) - w")
    axes[1].set_ylabel("Count")
    axes[1].set_xscale("log")
    axes[1].grid(alpha=0.2)

    fig.suptitle("The true gap tail is small, but the raw d=4 closure ceiling is not")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "prime_vs_d4_closure_window.png", dpi=200)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_rows()
    basis = compute_basis(sorted({row.n for row in rows}))
    witness_cache = compute_gap_witness_cache(rows)

    witness_rows: list[dict[str, object]] = []
    for prime_value in sorted(witness_cache):
        witness = witness_cache[prime_value]
        witness_rows.append(
            {
                "p_prev": witness.p_prev,
                "p_n": witness.p_n,
                "gap": witness.gap,
                "winner": witness.winner,
                "winner_divisor_count": witness.winner_divisor_count,
                "prime_minus_winner": witness.prime_minus_winner,
                "composite_threat": "" if witness.composite_threat is None else witness.composite_threat,
                "composite_threat_minus_winner": "" if witness.composite_threat_minus_winner is None else witness.composite_threat_minus_winner,
            }
        )

    rowwise_results: list[dict[str, object]] = []
    for row in rows:
        witness = witness_cache[row.p_n]
        basis_row = basis[row.n]
        for variant_name in VARIANT_ORDER:
            seed = estimate_variant(variant_name, row.n, basis_row)
            abs_seed_minus_prime = abs(seed - row.p_n)
            abs_seed_minus_winner = abs(seed - witness.winner)
            rowwise_results.append(
                {
                    "dataset": row.dataset,
                    "dataset_label": DATASET_LABELS[row.dataset],
                    "row_id": row.row_id,
                    "family": row.family,
                    "decade_exponent": row.decade_exponent,
                    "n": row.n,
                    "p_n": row.p_n,
                    "variant": variant_name,
                    "seed": seed,
                    "seed_minus_prime": seed - row.p_n,
                    "abs_seed_minus_prime": abs_seed_minus_prime,
                    "winner": witness.winner,
                    "winner_divisor_count": witness.winner_divisor_count,
                    "seed_minus_winner": seed - witness.winner,
                    "abs_seed_minus_winner": abs_seed_minus_winner,
                    "witness_target_gain": abs_seed_minus_prime - abs_seed_minus_winner,
                    "p_prev": witness.p_prev,
                    "gap": witness.gap,
                    "prime_minus_winner": witness.prime_minus_winner,
                    "composite_threat": "" if witness.composite_threat is None else witness.composite_threat,
                    "composite_threat_minus_winner": "" if witness.composite_threat_minus_winner is None else witness.composite_threat_minus_winner,
                }
            )

    variant_summary = build_variant_summary(rowwise_results)
    dataset_variant_summary = build_dataset_variant_summary(rowwise_results)
    witness_summary = build_witness_summary(witness_cache)

    write_csv(
        OUTPUT_DIR / "prime_gap_witness_rows.csv",
        [
            "p_prev",
            "p_n",
            "gap",
            "winner",
            "winner_divisor_count",
            "prime_minus_winner",
            "composite_threat",
            "composite_threat_minus_winner",
        ],
        witness_rows,
    )
    write_csv(
        OUTPUT_DIR / "rowwise_results.csv",
        [
            "dataset",
            "dataset_label",
            "row_id",
            "family",
            "decade_exponent",
            "n",
            "p_n",
            "variant",
            "seed",
            "seed_minus_prime",
            "abs_seed_minus_prime",
            "winner",
            "winner_divisor_count",
            "seed_minus_winner",
            "abs_seed_minus_winner",
            "witness_target_gain",
            "p_prev",
            "gap",
            "prime_minus_winner",
            "composite_threat",
            "composite_threat_minus_winner",
        ],
        rowwise_results,
    )
    write_csv(
        OUTPUT_DIR / "variant_summary.csv",
        [
            "variant",
            "row_count",
            "d4_row_count",
            "median_abs_seed_minus_prime",
            "median_abs_seed_minus_winner",
            "median_witness_target_gain",
            "p90_abs_seed_minus_winner",
            "max_abs_seed_minus_winner",
            "coverage_le_4096",
            "coverage_le_65536",
            "coverage_le_1048576",
            "median_prime_minus_winner_d4",
            "median_composite_threat_minus_winner_d4",
        ],
        variant_summary,
    )
    write_csv(
        OUTPUT_DIR / "dataset_variant_summary.csv",
        [
            "dataset",
            "variant",
            "row_count",
            "median_abs_seed_minus_winner",
            "p90_abs_seed_minus_winner",
            "coverage_le_65536",
            "coverage_le_1048576",
            "median_witness_target_gain",
        ],
        dataset_variant_summary,
    )
    write_csv(
        OUTPUT_DIR / "witness_summary.csv",
        [
            "prime_count",
            "d4_share",
            "median_gap",
            "median_prime_minus_winner",
            "p90_prime_minus_winner",
            "median_composite_threat_minus_winner_d4",
            "p10_prime_position_inside_d4_closure",
            "median_prime_position_inside_d4_closure",
        ],
        witness_summary,
    )

    plot_radius_coverage(rowwise_results)
    plot_prime_vs_closure(witness_cache)


if __name__ == "__main__":
    main()
