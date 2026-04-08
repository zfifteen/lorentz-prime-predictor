#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "backbone_ratio_classics"
PLOTS_DIR = OUTPUT_DIR / "plots"

FIXED_C = -0.00016667
FIXED_K = 0.06500
NEGATIVE_TWO_THIRDS = "0.6666666666666666"

DATASET_ORDER = [
    "published_exact_grid_ge_1e4",
    "reproducible_exact_baseline",
    "reproducible_exact_stage_a",
    "reproducible_exact_stage_b",
]

DATASET_LABELS = {
    "published_exact_grid_ge_1e4": "published exact grid",
    "reproducible_exact_baseline": "reproducible exact baseline",
    "reproducible_exact_stage_a": "reproducible exact stage_a",
    "reproducible_exact_stage_b": "reproducible exact stage_b",
}

COMPARATOR_ORDER = [
    "asym_c_backbone_ratio_k",
    "lpp_seed",
    "li_inverse_seed",
    "axler_three_term_point_estimate",
    "cipolla_one_over_log_sq",
    "cipolla_one_over_log",
    "pnt_two_term",
    "pnt_first_order",
]

COMPARATOR_COLORS = {
    "asym_c_backbone_ratio_k": "#2B8A3E",
    "lpp_seed": "#0B7285",
    "li_inverse_seed": "#6741D9",
    "axler_three_term_point_estimate": "#F08C00",
    "cipolla_one_over_log_sq": "#1C7ED6",
    "cipolla_one_over_log": "#74C0FC",
    "pnt_two_term": "#868E96",
    "pnt_first_order": "#495057",
}


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


def compute_basis(unique_n: list[int]) -> dict[int, tuple[float, float, float, float, float, float]]:
    basis: dict[int, tuple[float, float, float, float, float, float]] = {}
    for n in unique_n:
        precision = max(256, int(gp.log2(n)) + 256)
        with gp.context(gp.get_context(), precision=precision):
            n_mp = gp.mpfr(n)
            ln_n_mp = gp.log(n_mp)
            ln_ln_n_mp = gp.log(ln_n_mp)
            core = ln_n_mp + ln_ln_n_mp - 1
            one_over_log = (ln_ln_n_mp - 2) / ln_n_mp
            pnt = n_mp * (core + one_over_log)
            if pnt <= 0:
                pnt = n_mp
            ln_p_mp = gp.log(pnt)
            ln_ln_p_mp = gp.log(ln_p_mp)
            d_basis = pnt * ((ln_p_mp / gp.exp(gp.mpfr(4))) ** 2)
            k_basis = pnt ** gp.mpfr(NEGATIVE_TWO_THIRDS)
            basis[n] = (
                float(pnt),
                float(d_basis),
                float(k_basis),
                float(ln_n_mp),
                float(ln_ln_n_mp),
                float(ln_p_mp),
            )
    return basis


def c_asymptotic(ln_p: float) -> float:
    ln_ln_p = math.log(ln_p)
    polynomial = (ln_ln_p**2) - (6.0 * ln_ln_p) + 11.0
    return -((math.e**8) * polynomial) / (2.0 * (ln_p**5))


def k_backbone_ratio(pnt: float, n_value: int) -> float:
    density_backbone = pnt / n_value
    return 1.0 / (math.e**2 * (2.0 - ((math.e**2) / density_backbone)))


def fixed_lpp_seed(n_value: int, basis_row: tuple[float, float, float, float, float, float]) -> int:
    pnt, d_basis, k_basis, _, _, ln_p = basis_row
    estimate = math.floor(pnt + (FIXED_C * d_basis) + (FIXED_K * k_basis) + 0.5)
    if estimate <= 0:
        estimate = math.floor(pnt + 0.5)
    return estimate


def asym_c_backbone_ratio_seed(n_value: int, basis_row: tuple[float, float, float, float, float, float]) -> int:
    pnt, d_basis, k_basis, _, _, ln_p = basis_row
    c_value = c_asymptotic(ln_p)
    k_value = k_backbone_ratio(pnt, n_value)
    estimate = math.floor(pnt + (c_value * d_basis) + (k_value * k_basis) + 0.5)
    if estimate <= 0:
        estimate = math.floor(pnt + 0.5)
    return estimate


def li_inverse_seed(n_value: int) -> int:
    mp.mp.dps = 100
    ln_n = math.log(n_value)
    ln_ln_n = math.log(ln_n)
    seed = mp.mpf(n_value * (ln_n + ln_ln_n - 1.0 + (ln_ln_n - 2.0) / ln_n))
    target = mp.mpf(n_value)
    for _ in range(8):
        seed -= (mp.li(seed) - target) * mp.log(seed)
    return int(gp.mpz(seed + 0.5))


def classical_seed(comparator_name: str, n_value: int) -> int:
    ln_n = math.log(n_value)
    ln_ln_n = math.log(ln_n)
    base = ln_n + ln_ln_n - 1.0
    log_term = (ln_ln_n - 2.0) / ln_n
    log_sq_term = ((ln_ln_n * ln_ln_n) - 6.0 * ln_ln_n + 11.0) / (2.0 * ln_n * ln_n)
    log_cu_term = ((ln_ln_n**3) - 9.0 * (ln_ln_n**2) + 23.0 * ln_ln_n - 11.0) / (6.0 * (ln_n**3))

    if comparator_name == "pnt_first_order":
        value = n_value * ln_n
    elif comparator_name == "pnt_two_term":
        value = n_value * base
    elif comparator_name == "cipolla_one_over_log":
        value = n_value * (base + log_term)
    elif comparator_name == "cipolla_one_over_log_sq":
        value = n_value * (base + log_term - log_sq_term)
    elif comparator_name == "axler_three_term_point_estimate":
        value = n_value * (base + log_term - log_sq_term + log_cu_term)
    else:
        raise ValueError(f"unknown classical comparator: {comparator_name}")
    return int(gp.mpz(value + 0.5))


def compute_seed(
    comparator_name: str,
    n_value: int,
    basis_row: tuple[float, float, float, float, float, float],
) -> int:
    if comparator_name == "asym_c_backbone_ratio_k":
        return asym_c_backbone_ratio_seed(n_value, basis_row)
    if comparator_name == "lpp_seed":
        return fixed_lpp_seed(n_value, basis_row)
    if comparator_name == "li_inverse_seed":
        return li_inverse_seed(n_value)
    return classical_seed(comparator_name, n_value)


def evaluate(rows: list[tuple[str, int, int]], basis: dict[int, tuple[float, float, float, float, float, float]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    row_records: list[dict[str, float | int | str]] = []
    summary_records: list[dict[str, float | str]] = []

    for comparator_name in COMPARATOR_ORDER:
        for dataset_name in DATASET_ORDER:
            dataset_rows = [(n, p_n) for ds, n, p_n in rows if ds == dataset_name]
            errors: list[float] = []
            for n_value, p_n in dataset_rows:
                seed = compute_seed(comparator_name, n_value, basis[n_value])
                rel_ppm = abs(seed - p_n) / p_n * 1e6
                errors.append(rel_ppm)
                row_records.append(
                    {
                        "config": comparator_name,
                        "dataset": dataset_name,
                        "n": n_value,
                        "log10_n": math.log10(n_value),
                        "rel_ppm": rel_ppm,
                    }
                )
            summary_records.append(
                {
                    "config": comparator_name,
                    "dataset": dataset_name,
                    "max_rel_ppm": float(max(errors)),
                    "mean_rel_ppm": float(statistics.fmean(errors)),
                    "median_rel_ppm": float(statistics.median(errors)),
                }
            )

    return pd.DataFrame.from_records(row_records), pd.DataFrame.from_records(summary_records)


def build_published_point_comparison(rowwise: pd.DataFrame) -> pd.DataFrame:
    subset = rowwise[rowwise["dataset"] == "published_exact_grid_ge_1e4"].copy()
    pivot = subset.pivot(index=["n", "log10_n"], columns="config", values="rel_ppm").reset_index().sort_values("n")
    pivot.columns.name = None
    return pivot


def build_baseline_decade_summary(rowwise: pd.DataFrame) -> pd.DataFrame:
    subset = rowwise[rowwise["dataset"] == "reproducible_exact_baseline"].copy()
    subset["decade"] = np.floor(subset["log10_n"]).astype(int)
    records: list[dict[str, float | int | str]] = []
    for comparator_name in COMPARATOR_ORDER:
        config_subset = subset[subset["config"] == comparator_name]
        for decade, group in config_subset.groupby("decade", sort=True):
            rel = group["rel_ppm"].to_numpy(dtype=np.float64)
            records.append(
                {
                    "config": comparator_name,
                    "decade": int(decade),
                    "count": int(len(rel)),
                    "max_rel_ppm": float(np.max(rel)),
                    "mean_rel_ppm": float(np.mean(rel)),
                    "median_rel_ppm": float(np.median(rel)),
                }
            )
    return pd.DataFrame.from_records(records).sort_values(["config", "decade"]).reset_index(drop=True)


def write_report(summary: pd.DataFrame, output_path: Path) -> None:
    lines = [
        "# Backbone-ratio vs Classics",
        "",
        "Closed-form seed benchmark comparing `asym_c_backbone_ratio_k` against the current `lpp_seed` baseline and the classical seed formulas.",
        "",
    ]
    metrics = ["max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"]
    for dataset_name in DATASET_ORDER:
        lines.append(f"## {DATASET_LABELS[dataset_name]}")
        lines.append("")
        dataset_summary = summary[summary["dataset"] == dataset_name].copy()
        for metric in metrics:
            best_row = dataset_summary.sort_values(metric, kind="stable").iloc[0]
            lines.append(f"- best {metric.replace('_', ' ')}: `{best_row['config']}` = `{float(best_row[metric]):.6f}`")
        lines.append("")
        lines.append("| Comparator | Max ppm | Mean ppm | Median ppm |")
        lines.append("| --- | ---: | ---: | ---: |")
        ordered = dataset_summary.set_index("config").loc[COMPARATOR_ORDER].reset_index()
        for _, row in ordered.iterrows():
            lines.append(
                f"| {row['config']} | {float(row['max_rel_ppm']):.6f} | {float(row['mean_rel_ppm']):.6f} | {float(row['median_rel_ppm']):.6f} |"
            )
        lines.append("")
    output_path.write_text("\n".join(lines) + "\n")


def plot_summary(summary: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.8), sharey=False)
    metrics = ["max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"]
    x = np.arange(len(DATASET_ORDER))
    width = 0.1

    for ax, metric in zip(axes, metrics):
        for idx, comparator_name in enumerate(COMPARATOR_ORDER):
            bars = []
            for dataset_name in DATASET_ORDER:
                value = float(
                    summary[(summary["config"] == comparator_name) & (summary["dataset"] == dataset_name)][metric].iloc[0]
                )
                bars.append(value)
            ax.bar(
                x + ((idx - 3.5) * width),
                bars,
                width=width,
                color=COMPARATOR_COLORS[comparator_name],
                label=comparator_name,
            )
        ax.set_xticks(x, [DATASET_LABELS[name].replace("reproducible exact ", "").replace("published exact grid", "published") for name in DATASET_ORDER], rotation=20)
        ax.set_title(metric.replace("_", " "))
        ax.grid(True, axis="y", alpha=0.25)

    axes[0].set_ylabel("ppm")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_published_points(points: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 6))
    for comparator_name in COMPARATOR_ORDER:
        ax.plot(
            points["log10_n"],
            points[comparator_name],
            marker="o",
            linewidth=2,
            color=COMPARATOR_COLORS[comparator_name],
            label=comparator_name,
        )
    ax.set_title("Published exact grid: backbone-ratio vs classics")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("relative error (ppm)")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_baseline_decades(summary: pd.DataFrame, output_path: Path) -> None:
    focus_order = [
        "asym_c_backbone_ratio_k",
        "lpp_seed",
        "li_inverse_seed",
        "axler_three_term_point_estimate",
        "cipolla_one_over_log_sq",
    ]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.8), sharex=True, sharey=False)
    metrics = ["max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"]
    for ax, metric in zip(axes, metrics):
        for comparator_name in focus_order:
            subset = summary[summary["config"] == comparator_name]
            ax.plot(
                subset["decade"],
                subset[metric],
                marker="o",
                linewidth=2,
                color=COMPARATOR_COLORS[comparator_name],
                label=comparator_name,
            )
        ax.set_title(metric.replace("_", " "))
        ax.set_xlabel("decade of n")
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel("ppm")
    axes[0].legend(fontsize=8)
    fig.suptitle("Baseline exact set by decade")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[str, int, int]] = []
    rows.extend(load_known_primes_md(DATA_DIR / "KNOWN_PRIMES.md"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e4_1e12.csv", "reproducible_exact_baseline"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e13_1e14.csv", "reproducible_exact_stage_a"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e15_1e16.csv", "reproducible_exact_stage_b"))

    basis = compute_basis(sorted({n for _, n, _ in rows}))
    rowwise, summary = evaluate(rows, basis)
    published_points = build_published_point_comparison(rowwise)
    baseline_decades = build_baseline_decade_summary(rowwise)

    rowwise.to_csv(OUTPUT_DIR / "rowwise.csv", index=False, lineterminator="\n")
    summary.to_csv(OUTPUT_DIR / "summary.csv", index=False, lineterminator="\n")
    published_points.to_csv(OUTPUT_DIR / "published_exact_point_comparison.csv", index=False, lineterminator="\n")
    baseline_decades.to_csv(OUTPUT_DIR / "baseline_decade_summary.csv", index=False, lineterminator="\n")
    write_report(summary, OUTPUT_DIR / "report.md")

    plot_summary(summary, PLOTS_DIR / "summary.png")
    plot_published_points(published_points, PLOTS_DIR / "published_exact_points.png")
    plot_baseline_decades(baseline_decades, PLOTS_DIR / "baseline_decades.png")

    print(OUTPUT_DIR / "summary.csv")
    print(OUTPUT_DIR / "report.md")


if __name__ == "__main__":
    main()
