#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "c_derivation_probe"
PLOTS_DIR = OUTPUT_DIR / "plots"

CURRENT_C = -0.00016667
CURRENT_K = 0.06500
NEGATIVE_TWO_THIRDS = "0.6666666666666666"

DATASET_ORDER = [
    "published_exact_grid_ge_1e4",
    "reproducible_exact_baseline",
    "reproducible_exact_stage_a",
    "reproducible_exact_stage_b",
]

DATASET_LABELS = {
    "published_exact_grid_ge_1e4": "published exact grid (n >= 10^4)",
    "reproducible_exact_baseline": "reproducible exact baseline",
    "reproducible_exact_stage_a": "reproducible exact stage_a",
    "reproducible_exact_stage_b": "reproducible exact stage_b",
}

DATASET_COLORS = {
    "published_exact_grid_ge_1e4": "#d62728",
    "reproducible_exact_baseline": "#1f77b4",
    "reproducible_exact_stage_a": "#2ca02c",
    "reproducible_exact_stage_b": "#ff7f0e",
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


def compute_basis(unique_n: list[int]) -> dict[int, tuple[float, float, float, float, float]]:
    basis: dict[int, tuple[float, float, float, float, float]] = {}
    for n in unique_n:
        precision = max(256, int(gp.log2(n)) + 256)
        with gp.context(gp.get_context(), precision=precision):
            n_mp = gp.mpfr(n)
            ln_n = gp.log(n_mp)
            ln_ln_n = gp.log(ln_n)
            pnt = n_mp * (ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n))
            if pnt <= 0:
                pnt = n_mp
            e_fourth = gp.exp(gp.mpfr(4))
            d_basis = pnt * ((gp.log(pnt) / e_fourth) ** 2)
            k_basis = pnt ** gp.mpfr(NEGATIVE_TWO_THIRDS)
            ln_p = gp.log(pnt)
            ln_ln_p = gp.log(ln_p)
            basis[n] = (
                float(pnt),
                float(d_basis),
                float(k_basis),
                float(ln_p),
                float(ln_ln_p),
            )
    return basis


def c_asymptotic(ln_p: float, ln_ln_p: float) -> float:
    polynomial = (ln_ln_p**2) - (6.0 * ln_ln_p) + 11.0
    return -((math.e**8) * polynomial) / (2.0 * (ln_p**5))


def _round_half_up_positive(value: float | mp.mpf) -> int:
    return int(gp.mpz(value + 0.5))


def li_inverse_seed(n_value: int) -> int:
    mp.mp.dps = 100
    ln_n = math.log(n_value)
    ln_ln_n = math.log(ln_n)
    start = n_value * (ln_n + ln_ln_n - 1.0 + (ln_ln_n - 2.0) / ln_n)
    seed = mp.mpf(start)
    target = mp.mpf(n_value)
    for _ in range(8):
        seed -= (mp.li(seed) - target) * mp.log(seed)
    return _round_half_up_positive(seed)


def evaluate_configs(
    frame: pd.DataFrame,
    basis: dict[int, tuple[float, float, float, float, float]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    configs = [
        ("fixed_c", lambda log10_n, ln_p, ln_ln_p: CURRENT_C),
        ("asymptotic_c", lambda log10_n, ln_p, ln_ln_p: c_asymptotic(ln_p, ln_ln_p)),
    ]

    row_records: list[dict[str, float | str]] = []
    summary_records: list[dict[str, float | str]] = []

    for config_name, c_fn in configs:
        for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
            errors: list[float] = []
            c_values: list[float] = []
            for n, p_n in zip(group["n"], group["p_n"]):
                pnt, d_basis, k_basis, ln_p, ln_ln_p = basis[int(n)]
                log10_n = math.log10(int(n))
                c_value = c_fn(log10_n, ln_p, ln_ln_p)
                estimate = math.floor(pnt + (c_value * d_basis) + (CURRENT_K * k_basis) + 0.5)
                rel_ppm = abs(estimate - int(p_n)) / int(p_n) * 1e6
                errors.append(rel_ppm)
                c_values.append(c_value)
                row_records.append(
                    {
                        "config": config_name,
                        "dataset": dataset_name,
                        "n": int(n),
                        "log10_n": log10_n,
                        "c_value": c_value,
                        "rel_ppm": rel_ppm,
                    }
                )

            summary_records.append(
                {
                    "config": config_name,
                    "dataset": dataset_name,
                    "max_rel_ppm": float(max(errors)),
                    "mean_rel_ppm": float(np.mean(errors)),
                    "median_rel_ppm": float(np.median(errors)),
                    "c_min": float(min(c_values)),
                    "c_max": float(max(c_values)),
                }
            )

    for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
        errors: list[float] = []
        for n, p_n in zip(group["n"], group["p_n"]):
            estimate = li_inverse_seed(int(n))
            rel_ppm = abs(estimate - int(p_n)) / int(p_n) * 1e6
            errors.append(rel_ppm)
            row_records.append(
                {
                    "config": "li_inverse_seed",
                    "dataset": dataset_name,
                    "n": int(n),
                    "log10_n": math.log10(int(n)),
                    "c_value": math.nan,
                    "rel_ppm": rel_ppm,
                }
            )
        summary_records.append(
            {
                "config": "li_inverse_seed",
                "dataset": dataset_name,
                "max_rel_ppm": float(max(errors)),
                "mean_rel_ppm": float(np.mean(errors)),
                "median_rel_ppm": float(np.median(errors)),
                "c_min": math.nan,
                "c_max": math.nan,
            }
        )

    return pd.DataFrame.from_records(row_records), pd.DataFrame.from_records(summary_records)


def compute_required_c(frame: pd.DataFrame, basis: dict[int, tuple[float, float, float, float, float]]) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []
    for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
        for n, p_n in zip(group["n"], group["p_n"]):
            pnt, d_basis, k_basis, _, _ = basis[int(n)]
            c_required = (int(p_n) - pnt - (CURRENT_K * k_basis)) / d_basis
            records.append(
                {
                    "dataset": dataset_name,
                    "n": int(n),
                    "log10_n": math.log10(int(n)),
                    "c_required": float(c_required),
                }
            )
    return pd.DataFrame.from_records(records)


def plot_c_curves(required_c: pd.DataFrame, output_path: Path) -> None:
    sample_n = np.logspace(4, 24, 500)
    sample_log10 = np.log10(sample_n)
    ln_p = np.log(sample_n)
    ln_ln_p = np.log(ln_p)

    asym_c = np.array([c_asymptotic(lp, l2p) for lp, l2p in zip(ln_p, ln_ln_p)], dtype=np.float64)

    fig, ax = plt.subplots(figsize=(10, 6))
    for dataset_name in DATASET_ORDER:
        subset = required_c[required_c["dataset"] == dataset_name]
        ax.scatter(
            subset["log10_n"],
            subset["c_required"],
            s=18,
            alpha=0.65,
            color=DATASET_COLORS[dataset_name],
            label=f"{DATASET_LABELS[dataset_name]} required c",
        )

    ax.plot(sample_log10, np.full_like(sample_log10, CURRENT_C), color="#111111", linewidth=2, label="fixed c")
    ax.plot(sample_log10, asym_c, color="#9467bd", linewidth=2, label="asymptotic c")
    ax.set_title("Required c versus scale, with derived c curves")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("c")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_summary(summary: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharey=False)
    metrics = ["max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"]
    configs = ["fixed_c", "asymptotic_c", "li_inverse_seed"]
    x = np.arange(len(DATASET_ORDER))
    width = 0.24

    for ax, metric in zip(axes, metrics):
        for idx, config_name in enumerate(configs):
            bars = []
            for dataset_name in DATASET_ORDER:
                value = float(
                    summary[(summary["config"] == config_name) & (summary["dataset"] == dataset_name)][metric].iloc[0]
                )
                bars.append(value)
            ax.bar(x + ((idx - 1) * width), bars, width=width, label=config_name)
        ax.set_xticks(x, [name.replace("reproducible_exact_", "").replace("published_exact_grid_ge_1e4", "published") for name in DATASET_ORDER], rotation=20)
        ax.set_title(metric.replace("_", " "))
        ax.grid(True, axis="y", alpha=0.25)

    axes[0].set_ylabel("ppm")
    axes[0].legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def build_published_point_comparison(rowwise: pd.DataFrame) -> pd.DataFrame:
    subset = rowwise[rowwise["dataset"] == "published_exact_grid_ge_1e4"].copy()
    pivot = (
        subset.pivot(index=["n", "log10_n"], columns="config", values="rel_ppm")
        .reset_index()
        .sort_values("n")
    )
    pivot.columns.name = None
    return pivot


def build_published_cutoff_comparison(rowwise: pd.DataFrame) -> pd.DataFrame:
    subset = rowwise[rowwise["dataset"] == "published_exact_grid_ge_1e4"].copy()
    records: list[dict[str, float | str]] = []
    for cutoff in sorted(subset["n"].unique().tolist()):
        cutoff_rows = subset[subset["n"] >= cutoff]
        for config_name, group in cutoff_rows.groupby("config", sort=False):
            records.append(
                {
                    "cutoff_n": int(cutoff),
                    "cutoff_log10_n": float(math.log10(int(cutoff))),
                    "config": config_name,
                    "max_rel_ppm": float(group["rel_ppm"].max()),
                    "mean_rel_ppm": float(group["rel_ppm"].mean()),
                    "median_rel_ppm": float(group["rel_ppm"].median()),
                }
            )
    return pd.DataFrame.from_records(records)


def plot_published_point_comparison(points: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for config_name, color in [
        ("fixed_c", "#111111"),
        ("asymptotic_c", "#9467bd"),
        ("li_inverse_seed", "#1f77b4"),
    ]:
        ax.plot(
            points["log10_n"],
            points[config_name],
            marker="o",
            linewidth=2,
            color=color,
            label=config_name,
        )
    ax.set_title("Published exact grid: seed ppm by scale")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("relative error (ppm)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_published_cutoff_comparison(cutoffs: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharex=True)
    metrics = ["max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"]
    for ax, metric in zip(axes, metrics):
        for config_name, color in [
            ("fixed_c", "#111111"),
            ("asymptotic_c", "#9467bd"),
            ("li_inverse_seed", "#1f77b4"),
        ]:
            subset = cutoffs[cutoffs["config"] == config_name].sort_values("cutoff_n")
            ax.plot(
                subset["cutoff_log10_n"],
                subset[metric],
                marker="o",
                linewidth=2,
                color=color,
                label=config_name,
            )
        ax.set_title(metric.replace("_", " "))
        ax.set_xlabel("start at log10(n)")
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel("ppm")
    axes[0].legend()
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

    frame = pd.DataFrame(rows, columns=["dataset", "n", "p_n"])
    frame["dataset"] = pd.Categorical(frame["dataset"], categories=DATASET_ORDER, ordered=True)
    frame = frame.sort_values(["dataset", "n"]).reset_index(drop=True)

    basis = compute_basis(sorted(frame["n"].unique().tolist()))
    required_c = compute_required_c(frame, basis)
    rowwise, summary = evaluate_configs(frame, basis)
    published_points = build_published_point_comparison(rowwise)
    published_cutoffs = build_published_cutoff_comparison(rowwise)

    required_c.to_csv(OUTPUT_DIR / "required_c_by_row.csv", index=False, lineterminator="\n")
    rowwise.to_csv(OUTPUT_DIR / "c_probe_rowwise.csv", index=False, lineterminator="\n")
    summary.to_csv(OUTPUT_DIR / "c_probe_summary.csv", index=False, lineterminator="\n")
    published_points.to_csv(OUTPUT_DIR / "published_exact_point_comparison.csv", index=False, lineterminator="\n")
    published_cutoffs.to_csv(OUTPUT_DIR / "published_exact_cutoff_comparison.csv", index=False, lineterminator="\n")

    plot_c_curves(required_c, PLOTS_DIR / "c_required_and_derived_curves.png")
    plot_summary(summary, PLOTS_DIR / "c_probe_summary.png")
    plot_published_point_comparison(published_points, PLOTS_DIR / "published_exact_point_comparison.png")
    plot_published_cutoff_comparison(published_cutoffs, PLOTS_DIR / "published_exact_cutoff_comparison.png")

    print(f"Wrote required c rows to {OUTPUT_DIR / 'required_c_by_row.csv'}")
    print(f"Wrote probe rows to {OUTPUT_DIR / 'c_probe_rowwise.csv'}")
    print(f"Wrote summary to {OUTPUT_DIR / 'c_probe_summary.csv'}")


if __name__ == "__main__":
    main()
