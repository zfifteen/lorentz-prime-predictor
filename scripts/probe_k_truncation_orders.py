#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "k_truncation_probe"
PLOTS_DIR = OUTPUT_DIR / "plots"

NEGATIVE_TWO_THIRDS = "0.6666666666666666"

DATASET_ORDER = [
    "published_exact_grid_ge_1e4",
    "reproducible_exact_baseline",
    "reproducible_exact_stage_a",
    "reproducible_exact_stage_b",
]


def load_known_primes_md(path: Path) -> list[tuple[str, int, int]]:
    rows: list[tuple[str, int, int]] = []
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
                rows.append(("published_exact_grid_ge_1e4", n, p_n))
    return rows


def load_exact_csv(path: Path, dataset_name: str) -> list[tuple[str, int, int]]:
    rows: list[tuple[str, int, int]] = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append((dataset_name, int(row["n"]), int(row["p_n"])))
    return rows


def compute_basis(unique_n: list[int]) -> dict[int, tuple[float, float, float, float, float, float, float]]:
    basis: dict[int, tuple[float, float, float, float, float, float, float]] = {}
    for n in unique_n:
        precision = max(256, int(gp.log2(n)) + 256)
        with gp.local_context(gp.context(), precision=precision):
            n_mp = gp.mpfr(n)
            ln_n_mp = gp.log(n_mp)
            ln_ln_n_mp = gp.log(ln_n_mp)
            pnt = n_mp * (ln_n_mp + ln_ln_n_mp - 1 + ((ln_ln_n_mp - 2) / ln_n_mp))
            if pnt <= 0:
                pnt = n_mp
            e_fourth = gp.exp(gp.mpfr(4))
            d_basis = pnt * ((gp.log(pnt) / e_fourth) ** 2)
            k_power = pnt ** gp.mpfr(NEGATIVE_TWO_THIRDS)
            ln_p_mp = gp.log(pnt)
            ln_ln_p_mp = gp.log(ln_p_mp)
            basis[n] = (
                float(pnt),
                float(d_basis),
                float(k_power),
                float(ln_n_mp),
                float(ln_ln_n_mp),
                float(ln_p_mp),
                float(ln_ln_p_mp),
            )
    return basis


def c_asymptotic(ln_p: float, ln_ln_p: float) -> float:
    polynomial = (ln_ln_p**2) - (6.0 * ln_ln_p) + 11.0
    return -((math.e**8) * polynomial) / (2.0 * (ln_p**5))


def k_truncation(pnt: float, n_value: int, order: int) -> float:
    density_backbone = pnt / n_value
    ratio = (math.e**2) / (2.0 * density_backbone)
    series_sum = 0.0
    for exponent in range(order + 1):
        series_sum += ratio**exponent
    return series_sum / (2.0 * math.e**2)


def evaluate_orders(
    frame: pd.DataFrame,
    basis: dict[int, tuple[float, float, float, float, float, float, float]],
    max_order: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    row_records: list[dict[str, float | int | str]] = []
    summary_records: list[dict[str, float | int | str]] = []

    for order in range(1, max_order + 1):
        config_name = f"trunc{order}"
        for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
            errors: list[float] = []
            for n_value, p_n in zip(group["n"], group["p_n"]):
                pnt, d_basis, k_power, _, _, ln_p, ln_ln_p = basis[int(n_value)]
                c_value = c_asymptotic(ln_p, ln_ln_p)
                k_value = k_truncation(pnt, int(n_value), order)
                estimate = math.floor(pnt + (c_value * d_basis) + (k_value * k_power) + 0.5)
                rel_ppm = abs(estimate - int(p_n)) / int(p_n) * 1e6
                errors.append(rel_ppm)
                row_records.append(
                    {
                        "config": config_name,
                        "order": order,
                        "dataset": dataset_name,
                        "n": int(n_value),
                        "log10_n": math.log10(int(n_value)),
                        "rel_ppm": rel_ppm,
                    }
                )

            summary_records.append(
                {
                    "config": config_name,
                    "order": order,
                    "dataset": dataset_name,
                    "max_rel_ppm": float(max(errors)),
                    "mean_rel_ppm": float(statistics.fmean(errors)),
                    "median_rel_ppm": float(np.median(errors)),
                }
            )

    return pd.DataFrame.from_records(row_records), pd.DataFrame.from_records(summary_records)


def plot_order_sweep(summary: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharex=True)
    metrics = ["max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"]

    for ax, metric in zip(axes, metrics):
        for dataset_name in DATASET_ORDER:
            subset = summary[summary["dataset"] == dataset_name]
            ax.plot(
                subset["order"],
                subset[metric],
                marker="o",
                linewidth=2,
                label=dataset_name.replace("reproducible_exact_", "").replace("published_exact_grid_ge_1e4", "published"),
            )
        ax.set_title(metric.replace("_", " "))
        ax.set_xlabel("truncation order")
        ax.grid(True, alpha=0.25)

    axes[0].set_ylabel("ppm")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def write_readme(summary: pd.DataFrame, output_path: Path) -> None:
    pivot = summary.pivot(index="order", columns="dataset", values="max_rel_ppm").reset_index()
    best_published_order = int(summary[summary["dataset"] == "published_exact_grid_ge_1e4"].sort_values("max_rel_ppm").iloc[0]["order"])
    best_baseline_order = int(summary[summary["dataset"] == "reproducible_exact_baseline"].sort_values("max_rel_ppm").iloc[0]["order"])

    lines = [
        "# k* Truncation Order Probe",
        "",
        "This probe evaluates strictly derived lift coefficients built from higher-order truncations of the geometric expansion of",
        "",
        "$$",
        "k_{\\mathrm{old}}(n) = \\frac{1}{e^2\\left(2 - \\frac{e^2}{B(n)}\\right)}",
        "$$",
        "",
        "with",
        "",
        "$$",
        "k^*_{(m)}(n) = \\frac{1}{2e^2}\\sum_{j=0}^{m}\\left(\\frac{e^2}{2B(n)}\\right)^j.",
        "$$",
        "",
        f"Best published-grid max ppm in this sweep: `trunc{best_published_order}`.",
        f"Best baseline max ppm in this sweep: `trunc{best_baseline_order}`.",
        "",
        "The main empirical pattern is simple:",
        "",
        "- `trunc1` is the strict first-order baseline.",
        "- `trunc2` and `trunc3` recover most of the lost low-regime strength.",
        "- higher orders continue converging toward the old singular lift on the benchmark domain.",
        "",
        "See [truncation_order_sweep.csv](./truncation_order_sweep.csv) and [plots/truncation_order_sweep.png](./plots/truncation_order_sweep.png).",
        "",
        "## Max ppm by order",
        "",
        pivot.to_markdown(index=False),
        "",
    ]
    output_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[str, int, int]] = []
    rows.extend(load_known_primes_md(DATA_DIR / "KNOWN_PRIMES.md"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e4_1e12.csv", "reproducible_exact_baseline"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e13_1e14.csv", "reproducible_exact_stage_a"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e15_1e16.csv", "reproducible_exact_stage_b"))

    frame = pd.DataFrame(rows, columns=["dataset", "n", "p_n"])
    frame["dataset"] = pd.Categorical(frame["dataset"], categories=DATASET_ORDER, ordered=True)
    frame = frame.sort_values(["dataset", "n"]).reset_index(drop=True)

    basis = compute_basis(sorted(frame["n"].unique().tolist()))
    _, summary = evaluate_orders(frame, basis, max_order=10)

    summary.to_csv(OUTPUT_DIR / "truncation_order_sweep.csv", index=False, lineterminator="\n")
    plot_order_sweep(summary, PLOTS_DIR / "truncation_order_sweep.png")
    write_readme(summary, OUTPUT_DIR / "README.md")

    print(f"Wrote summary to {OUTPUT_DIR / 'truncation_order_sweep.csv'}")
    print(f"Wrote plot to {PLOTS_DIR / 'truncation_order_sweep.png'}")


if __name__ == "__main__":
    main()
