#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "nonheuristic_complexity_ladder"
PLOTS_DIR = OUTPUT_DIR / "plots"

DATASET_ORDER = [
    "published_exact_grid_ge_1e4",
    "reproducible_exact_stage_a",
    "reproducible_exact_stage_b",
]

DATASET_LABELS = {
    "published_exact_grid_ge_1e4": "published exact grid",
    "reproducible_exact_stage_a": "stage_a",
    "reproducible_exact_stage_b": "stage_b",
}

VARIANT_ORDER = [
    "lead3",
    "lead34",
    "lead345",
    "lead_closed",
    "cipolla_log3_repacked",
    "cipolla_log4_repacked",
    "cipolla_log5_repacked",
    "li_inverse_seed",
]

VARIANT_LABELS = {
    "lead3": "lead3",
    "lead34": "lead34",
    "lead345": "lead345",
    "lead_closed": "lead_closed",
    "cipolla_log3_repacked": "full log3",
    "cipolla_log4_repacked": "full log4",
    "cipolla_log5_repacked": "full log5",
    "li_inverse_seed": "li_inverse",
}

CIPOLLA_RAW_POLYNOMIALS = {
    3: [-131, 84, -21, 2],
    4: [2666, -1908, 588, -92, 6],
    5: [-81534, 62860, -22020, 4380, -490, 24],
}


def load_known_primes_md(path: Path) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    with path.open() as handle:
        for line in handle:
            if not line.startswith("|"):
                continue
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) < 4:
                continue
            try:
                n = int(parts[0].replace(",", "").replace("_", ""))
                p_n = int(parts[2].replace(",", "").replace("_", ""))
            except ValueError:
                continue
            if n >= 10_000:
                rows.append(
                    {
                        "dataset": "published_exact_grid_ge_1e4",
                        "n": n,
                        "p_n": p_n,
                    }
                )
    return rows


def load_exact_csv(path: Path, dataset_name: str) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "dataset": dataset_name,
                    "n": int(row["n"]),
                    "p_n": int(row["p_n"]),
                }
            )
    return rows


def li_inverse_seed(n_value: int) -> int:
    mp.mp.dps = 100
    ln_n = math.log(n_value)
    ln_ln_n = math.log(ln_n)
    start = n_value * (ln_n + ln_ln_n - 1.0 + (ln_ln_n - 2.0) / ln_n)
    seed = mp.mpf(start)
    target = mp.mpf(n_value)
    for _ in range(8):
        seed -= (mp.li(seed) - target) * mp.log(seed)
    return int(gp.mpz(seed + 0.5))


def compute_basis(unique_n_values: list[int]) -> dict[int, dict[str, float]]:
    basis: dict[int, dict[str, float]] = {}
    for n_value in unique_n_values:
        precision = max(256, int(gp.log2(n_value)) + 256)
        with gp.local_context(gp.context(), precision=precision):
            n_mp = gp.mpfr(n_value)
            ln_n = gp.log(n_mp)
            ln_ln_n = gp.log(ln_n)
            pnt = n_mp * (ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n))
            if pnt <= 0:
                pnt = n_mp
            ln_p = gp.log(pnt)
            ln_ln_p = gp.log(ln_p)
            backbone_ratio = pnt / n_mp
            basis[n_value] = {
                "P": float(pnt),
                "L": float(ln_n),
                "LL": float(ln_ln_n),
                "LP": float(ln_p),
                "LLP": float(ln_ln_p),
                "B": float(backbone_ratio),
            }
    return basis


def c_n_value(row: dict[str, float]) -> float:
    return -((row["LL"] ** 2) - 6.0 * row["LL"] + 11.0) / (
        2.0 * (row["L"] ** 2) * row["B"] * ((row["LP"] / (math.e**4)) ** 2)
    )


def cipolla_polynomial(order: int, ln_ln_n: float) -> float:
    coefficients = CIPOLLA_RAW_POLYNOMIALS[order]
    total = 0.0
    for power, coefficient in enumerate(coefficients):
        total += coefficient * (ln_ln_n**power)
    return total / math.factorial(order)


def exact_repacked_residual(row: dict[str, float], upto_order: int) -> float:
    n_value = row["P"] / row["B"]
    residual = 0.0
    for order in range(3, upto_order + 1):
        sign = 1.0 if order % 2 == 1 else -1.0
        residual += n_value * sign * cipolla_polynomial(order, row["LL"]) / (row["L"] ** order)
    return residual


def leading_log_residual(row: dict[str, float], upto_order: int) -> float:
    u = row["LL"] / row["L"]
    n_value = row["P"] / row["B"]
    total = 0.0
    for order in range(3, upto_order + 1):
        sign = 1.0 if order % 2 == 1 else -1.0
        total += sign * (u**order) / order
    return n_value * total


def leading_log_closed_residual(row: dict[str, float]) -> float:
    u = row["LL"] / row["L"]
    n_value = row["P"] / row["B"]
    return n_value * (math.log(1.0 + u) - u + (u**2) / 2.0)


def estimate_variant(variant_name: str, n_value: int, basis_row: dict[str, float]) -> int:
    if variant_name == "li_inverse_seed":
        return li_inverse_seed(n_value)

    pnt = basis_row["P"]
    ln_p = basis_row["LP"]
    c_value = c_n_value(basis_row)
    base = pnt + c_value * pnt * ((ln_p / (math.e**4)) ** 2)

    if variant_name == "lead3":
        residual = leading_log_residual(basis_row, 3)
    elif variant_name == "lead34":
        residual = leading_log_residual(basis_row, 4)
    elif variant_name == "lead345":
        residual = leading_log_residual(basis_row, 5)
    elif variant_name == "lead_closed":
        residual = leading_log_closed_residual(basis_row)
    elif variant_name == "cipolla_log3_repacked":
        residual = exact_repacked_residual(basis_row, 3)
    elif variant_name == "cipolla_log4_repacked":
        residual = exact_repacked_residual(basis_row, 4)
    elif variant_name == "cipolla_log5_repacked":
        residual = exact_repacked_residual(basis_row, 5)
    else:
        raise ValueError(f"unknown variant: {variant_name}")

    return math.floor(base + residual + 0.5)


def summarize(values: list[float]) -> dict[str, float]:
    arr = np.array(values, dtype=np.float64)
    return {
        "max_rel_ppm": float(arr.max()),
        "mean_rel_ppm": float(arr.mean()),
        "median_rel_ppm": float(np.median(arr)),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_summary(summary_rows: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), constrained_layout=True)
    colors = [
        "#868e96",
        "#5c7cfa",
        "#f59f00",
        "#12b886",
        "#74c0fc",
        "#4c6ef5",
        "#0b7285",
        "#6741d9",
    ]

    for ax, dataset_name in zip(axes, DATASET_ORDER):
        subset = [row for row in summary_rows if row["dataset"] == dataset_name]
        x = np.arange(len(subset))
        ax.bar(x, [float(row["max_rel_ppm"]) for row in subset], color=colors)
        ax.set_yscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels([VARIANT_LABELS[str(row["variant"])] for row in subset], rotation=25, ha="right")
        ax.set_title(DATASET_LABELS[dataset_name])
        ax.set_ylabel("max seed ppm")
        ax.grid(True, axis="y", alpha=0.25)

    fig.suptitle("Non-heuristic complexity ladder", fontsize=14)
    fig.savefig(PLOTS_DIR / "nonheuristic_complexity_ladder.png", dpi=180)
    plt.close(fig)


def write_readme(summary_rows: list[dict[str, object]]) -> None:
    def find(dataset_name: str, variant_name: str) -> dict[str, object]:
        return next(
            item
            for item in summary_rows
            if item["dataset"] == dataset_name and item["variant"] == variant_name
        )

    order4_stage_b = find("reproducible_exact_stage_b", "cipolla_log4_repacked")
    order5_stage_b = find("reproducible_exact_stage_b", "cipolla_log5_repacked")
    li_stage_b = find("reproducible_exact_stage_b", "li_inverse_seed")
    lead_closed_stage_b = find("reproducible_exact_stage_b", "lead_closed")

    lines = [
        "# Non-Heuristic Complexity Ladder",
        "",
        "This probe tests a narrow question: how simple can a fully derived large-regime residual be before it stops beating `li_inverse_seed`?",
        "",
        "The ladder is:",
        "",
        "1. leading-log order 3",
        "2. leading-log order 4",
        "3. leading-log order 5",
        "4. leading-log closed form",
        "5. full repacked order 3",
        "6. full repacked order 4",
        "7. full repacked order 5",
        "",
        "The leading-log family keeps only the highest-power `\\ell^k/L^k` term from each Cipolla order, where `\\ell = \\ln\\ln n` and `L = \\ln n`.",
        "",
        "The closed leading-log sum is",
        "",
        "$$ u = \\frac{\\ln\\ln n}{\\ln n} $$",
        "",
        "$$ n\\left(\\ln(1+u) - u + \\frac{u^2}{2}\\right) $$",
        "",
        "The full repacked family keeps the exact Cipolla polynomials through the stated order.",
        "",
        "## Strongest Finding",
        "",
        "The first rung in this non-heuristic ladder that beats `li_inverse_seed` on both exact large stages is the full repacked order-5 candidate.",
        "",
        f"- `stage_b` max ppm, leading-log closed form: `{float(lead_closed_stage_b['max_rel_ppm']):.6f}`",
        f"- `stage_b` max ppm, full repacked order 4: `{float(order4_stage_b['max_rel_ppm']):.6f}`",
        f"- `stage_b` max ppm, full repacked order 5: `{float(order5_stage_b['max_rel_ppm']):.6f}`",
        f"- `stage_b` max ppm, `li_inverse_seed`: `{float(li_stage_b['max_rel_ppm']):.6f}`",
        "",
        "So the large-stage win does not survive the leading-log simplification, and it does not survive the full order-4 truncation either. The exact first winning rung is full order 5.",
        "",
        "## Artifacts",
        "",
        "- [complexity_ladder_summary.csv](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/benchmarks/nonheuristic_complexity_ladder/complexity_ladder_summary.csv)",
        "- [nonheuristic_complexity_ladder.png](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/benchmarks/nonheuristic_complexity_ladder/plots/nonheuristic_complexity_ladder.png)",
        "",
    ]

    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_known_primes_md(DATA_DIR / "KNOWN_PRIMES.md")
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e13_1e14.csv", "reproducible_exact_stage_a"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e15_1e16.csv", "reproducible_exact_stage_b"))

    unique_n_values = sorted({int(row["n"]) for row in rows})
    basis = compute_basis(unique_n_values)

    summary_rows: list[dict[str, object]] = []
    for dataset_name in DATASET_ORDER:
        subset = [row for row in rows if row["dataset"] == dataset_name]
        for variant_name in VARIANT_ORDER:
            errors = []
            for row in subset:
                estimate = estimate_variant(variant_name, int(row["n"]), basis[int(row["n"])])
                p_n = int(row["p_n"])
                errors.append(abs(estimate - p_n) / p_n * 1e6)
            summary_rows.append(
                {
                    "dataset": dataset_name,
                    "variant": variant_name,
                    **summarize(errors),
                }
            )

    write_csv(
        OUTPUT_DIR / "complexity_ladder_summary.csv",
        ["dataset", "variant", "max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"],
        summary_rows,
    )
    plot_summary(summary_rows)
    write_readme(summary_rows)


if __name__ == "__main__":
    main()
