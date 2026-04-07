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
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "k_derivation_probe"
PLOTS_DIR = OUTPUT_DIR / "plots"

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


def c_asymptotic(ln_p: float, ln_ln_p: float) -> float:
    polynomial = (ln_ln_p**2) - (6.0 * ln_ln_p) + 11.0
    return -((math.e**8) * polynomial) / (2.0 * (ln_p**5))


def k_asym_n(ln_n: float, ln_ln_n: float, n_value: int, pnt: float) -> float:
    polynomial = ((ln_ln_n**3) - 9.0 * (ln_ln_n**2) + 23.0 * ln_ln_n - 11.0) / (6.0 * (ln_n**3))
    return (n_value * polynomial) / (pnt ** (2.0 / 3.0))


def k_asym_p(ln_p: float, ln_ln_p: float, pnt: float) -> float:
    polynomial = ((ln_ln_p**3) - 9.0 * (ln_ln_p**2) + 23.0 * ln_ln_p - 11.0) / (6.0 * (ln_p**3))
    return (pnt * polynomial) / (pnt ** (2.0 / 3.0))


def k_mild_ratio(ln_p: float) -> float:
    return 1.0 / (math.e**2 * (1.9 - (7.0 / ln_p)))


def k_backbone_ratio(pnt: float, n_value: int) -> float:
    density_backbone = pnt / n_value
    return 1.0 / (math.e**2 * (2.0 - ((math.e**2) / density_backbone)))


def k_regularized_ratio(pnt: float, n_value: int) -> float:
    density_backbone = pnt / n_value
    return 1.0 / (math.e**2 * (2.0 - ((math.e**2) / (density_backbone + math.e**2))))


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
            k_basis = pnt ** gp.mpfr(NEGATIVE_TWO_THIRDS)
            ln_p_mp = gp.log(pnt)
            ln_ln_p_mp = gp.log(ln_p_mp)
            basis[n] = (
                float(pnt),
                float(d_basis),
                float(k_basis),
                float(ln_n_mp),
                float(ln_ln_n_mp),
                float(ln_p_mp),
                float(ln_ln_p_mp),
            )
    return basis


def compute_required_k(frame: pd.DataFrame, basis: dict[int, tuple[float, float, float, float, float, float, float]]) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []
    for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
        for n, p_n in zip(group["n"], group["p_n"]):
            pnt, d_basis, k_basis, _, _, ln_p, ln_ln_p = basis[int(n)]
            c_value = c_asymptotic(ln_p, ln_ln_p)
            k_required = (int(p_n) - pnt - (c_value * d_basis)) / k_basis
            records.append(
                {
                    "dataset": dataset_name,
                    "n": int(n),
                    "log10_n": math.log10(int(n)),
                    "k_required": float(k_required),
                }
            )
    return pd.DataFrame.from_records(records)


def evaluate_configs(
    frame: pd.DataFrame,
    basis: dict[int, tuple[float, float, float, float, float, float, float]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    configs = [
        ("asym_c_fixed_k", "asym_c_fixed_k"),
        ("asym_c_mild_ratio_k", "asym_c_mild_ratio_k"),
        ("asym_c_backbone_ratio_k", "asym_c_backbone_ratio_k"),
        ("asym_c_regularized_ratio_k", "asym_c_regularized_ratio_k"),
        ("asym_c_k_n", "asym_c_k_n"),
        ("asym_c_k_p", "asym_c_k_p"),
        ("li_inverse_seed", "li_inverse_seed"),
    ]

    row_records: list[dict[str, float | str]] = []
    summary_records: list[dict[str, float | str]] = []

    for config_name, _ in configs:
        for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
            errors: list[float] = []
            k_values: list[float] = []
            for n, p_n in zip(group["n"], group["p_n"]):
                pnt, d_basis, k_basis, ln_n, ln_ln_n, ln_p, ln_ln_p = basis[int(n)]
                if config_name == "li_inverse_seed":
                    estimate = li_inverse_seed(int(n))
                    k_value = math.nan
                else:
                    c_value = c_asymptotic(ln_p, ln_ln_p)
                    if config_name == "asym_c_fixed_k":
                        k_value = CURRENT_K
                    elif config_name == "asym_c_mild_ratio_k":
                        k_value = k_mild_ratio(ln_p)
                    elif config_name == "asym_c_backbone_ratio_k":
                        k_value = k_backbone_ratio(pnt, int(n))
                    elif config_name == "asym_c_regularized_ratio_k":
                        k_value = k_regularized_ratio(pnt, int(n))
                    elif config_name == "asym_c_k_n":
                        k_value = k_asym_n(ln_n, ln_ln_n, int(n), pnt)
                    else:
                        k_value = k_asym_p(ln_p, ln_ln_p, pnt)
                    estimate = math.floor(pnt + (c_value * d_basis) + (k_value * k_basis) + 0.5)
                rel_ppm = abs(estimate - int(p_n)) / int(p_n) * 1e6
                errors.append(rel_ppm)
                k_values.append(k_value)
                row_records.append(
                    {
                        "config": config_name,
                        "dataset": dataset_name,
                        "n": int(n),
                        "log10_n": math.log10(int(n)),
                        "k_value": k_value,
                        "rel_ppm": rel_ppm,
                    }
                )

            finite_k = [value for value in k_values if not math.isnan(value)]
            summary_records.append(
                {
                    "config": config_name,
                    "dataset": dataset_name,
                    "max_rel_ppm": float(max(errors)),
                    "mean_rel_ppm": float(np.mean(errors)),
                    "median_rel_ppm": float(np.median(errors)),
                    "k_min": float(min(finite_k)) if finite_k else math.nan,
                    "k_max": float(max(finite_k)) if finite_k else math.nan,
                }
            )

    return pd.DataFrame.from_records(row_records), pd.DataFrame.from_records(summary_records)


def build_published_point_comparison(rowwise: pd.DataFrame) -> pd.DataFrame:
    subset = rowwise[rowwise["dataset"] == "published_exact_grid_ge_1e4"].copy()
    pivot = (
        subset.pivot(index=["n", "log10_n"], columns="config", values="rel_ppm")
        .reset_index()
        .sort_values("n")
    )
    pivot.columns.name = None
    return pivot


def build_baseline_decade_summary(rowwise: pd.DataFrame) -> pd.DataFrame:
    subset = rowwise[rowwise["dataset"] == "reproducible_exact_baseline"].copy()
    subset["decade"] = np.floor(subset["log10_n"]).astype(int)

    records: list[dict[str, float | int | str]] = []
    configs = ["asym_c_fixed_k", "asym_c_mild_ratio_k", "asym_c_backbone_ratio_k", "li_inverse_seed"]
    for config_name in configs:
        config_subset = subset[subset["config"] == config_name]
        for decade, group in config_subset.groupby("decade", sort=True):
            rel = group["rel_ppm"].to_numpy(dtype=np.float64)
            records.append(
                {
                    "config": config_name,
                    "decade": int(decade),
                    "count": int(len(rel)),
                    "max_rel_ppm": float(np.max(rel)),
                    "mean_rel_ppm": float(np.mean(rel)),
                    "median_rel_ppm": float(np.median(rel)),
                }
            )

    return pd.DataFrame.from_records(records).sort_values(["config", "decade"]).reset_index(drop=True)


def plot_required_k(required_k: pd.DataFrame, output_path: Path) -> None:
    sample_n = np.logspace(4, 24, 500)
    sample_log10 = np.log10(sample_n)
    ln_n = np.log(sample_n)
    ln_ln_n = np.log(ln_n)
    pnt = sample_n * (ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n))
    ln_p = np.log(pnt)
    ln_ln_p = np.log(ln_p)

    k_n_curve = np.array([k_asym_n(lnv, llnv, int(round(nv)), pv) for lnv, llnv, nv, pv in zip(ln_n, ln_ln_n, sample_n, pnt)], dtype=np.float64)
    k_p_curve = np.array([k_asym_p(lpv, llpv, pv) for lpv, llpv, pv in zip(ln_p, ln_ln_p, pnt)], dtype=np.float64)

    fig, ax = plt.subplots(figsize=(10, 6))
    for dataset_name in DATASET_ORDER:
        subset = required_k[required_k["dataset"] == dataset_name]
        ax.scatter(
            subset["log10_n"],
            subset["k_required"],
            s=18,
            alpha=0.65,
            color=DATASET_COLORS[dataset_name],
            label=f"{DATASET_LABELS[dataset_name]} required k*",
        )
    ax.plot(sample_log10, np.full_like(sample_log10, CURRENT_K), color="#111111", linewidth=2, label="fixed k*")
    ax.plot(
        sample_log10,
        np.array([k_mild_ratio(value) for value in ln_p], dtype=np.float64),
        color="#2ca02c",
        linewidth=2,
        label="mild ratio k*",
    )
    ax.plot(
        sample_log10,
        np.array([k_backbone_ratio(pv, int(round(nv))) for nv, pv in zip(sample_n, pnt)], dtype=np.float64),
        color="#20A060",
        linewidth=2,
        label="backbone ratio k*",
    )
    ax.plot(
        sample_log10,
        np.array([k_regularized_ratio(pv, int(round(nv))) for nv, pv in zip(sample_n, pnt)], dtype=np.float64),
        color="#17becf",
        linewidth=2,
        label="regularized ratio k*",
    )
    ax.plot(sample_log10, k_n_curve, color="#9467bd", linewidth=2, label="asymptotic k* from ln n")
    ax.plot(sample_log10, k_p_curve, color="#1f77b4", linewidth=2, label="asymptotic k* from ln P")
    ax.set_title("Required k* under asymptotic c, with derived k* curves")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("k*")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_published_points(points: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for config_name, color in [
        ("asym_c_fixed_k", "#111111"),
        ("asym_c_mild_ratio_k", "#2ca02c"),
        ("asym_c_backbone_ratio_k", "#20A060"),
        ("asym_c_regularized_ratio_k", "#17becf"),
        ("asym_c_k_n", "#9467bd"),
        ("asym_c_k_p", "#8c564b"),
        ("li_inverse_seed", "#1f77b4"),
    ]:
        ax.plot(points["log10_n"], points[config_name], marker="o", linewidth=2, color=color, label=config_name)
    ax.set_title("Published exact grid: asymptotic-c k* variants")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("relative error (ppm)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_summary(summary: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharey=False)
    metrics = ["max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"]
    configs = [
        "asym_c_fixed_k",
        "asym_c_mild_ratio_k",
        "asym_c_backbone_ratio_k",
        "asym_c_regularized_ratio_k",
        "asym_c_k_n",
        "asym_c_k_p",
        "li_inverse_seed",
    ]
    x = np.arange(len(DATASET_ORDER))
    width = 0.11

    for ax, metric in zip(axes, metrics):
        for idx, config_name in enumerate(configs):
            bars = []
            for dataset_name in DATASET_ORDER:
                value = float(
                    summary[(summary["config"] == config_name) & (summary["dataset"] == dataset_name)][metric].iloc[0]
                )
                bars.append(value)
            ax.bar(x + ((idx - 3.0) * width), bars, width=width, label=config_name)
        ax.set_xticks(
            x,
            [name.replace("reproducible_exact_", "").replace("published_exact_grid_ge_1e4", "published") for name in DATASET_ORDER],
            rotation=20,
        )
        ax.set_title(metric.replace("_", " "))
        ax.grid(True, axis="y", alpha=0.25)

    axes[0].set_ylabel("ppm")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_baseline_decades(summary: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharex=True, sharey=False)
    metrics = ["max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"]
    configs = [
        ("asym_c_fixed_k", "#111111"),
        ("asym_c_mild_ratio_k", "#2ca02c"),
        ("asym_c_backbone_ratio_k", "#20A060"),
        ("asym_c_regularized_ratio_k", "#17becf"),
        ("li_inverse_seed", "#1f77b4"),
    ]

    for ax, metric in zip(axes, metrics):
        for config_name, color in configs:
            subset = summary[summary["config"] == config_name]
            ax.plot(
                subset["decade"],
                subset[metric],
                marker="o",
                linewidth=2,
                color=color,
                label=config_name,
            )
        ax.set_title(metric.replace("_", " "))
        ax.set_xlabel("decade of n")
        ax.grid(True, alpha=0.25)

    axes[0].set_ylabel("ppm")
    axes[0].legend()
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

    frame = pd.DataFrame(rows, columns=["dataset", "n", "p_n"])
    frame["dataset"] = pd.Categorical(frame["dataset"], categories=DATASET_ORDER, ordered=True)
    frame = frame.sort_values(["dataset", "n"]).reset_index(drop=True)

    basis = compute_basis(sorted(frame["n"].unique().tolist()))
    required_k = compute_required_k(frame, basis)
    rowwise, summary = evaluate_configs(frame, basis)
    published_points = build_published_point_comparison(rowwise)
    baseline_decades = build_baseline_decade_summary(rowwise)

    required_k.to_csv(OUTPUT_DIR / "required_k_by_row.csv", index=False, lineterminator="\n")
    rowwise.to_csv(OUTPUT_DIR / "k_probe_rowwise.csv", index=False, lineterminator="\n")
    summary.to_csv(OUTPUT_DIR / "k_probe_summary.csv", index=False, lineterminator="\n")
    published_points.to_csv(OUTPUT_DIR / "published_exact_point_comparison.csv", index=False, lineterminator="\n")
    baseline_decades.to_csv(OUTPUT_DIR / "baseline_decade_summary.csv", index=False, lineterminator="\n")

    plot_required_k(required_k, PLOTS_DIR / "required_k_and_candidate_curves.png")
    plot_published_points(published_points, PLOTS_DIR / "published_exact_point_comparison.png")
    plot_summary(summary, PLOTS_DIR / "k_probe_summary.png")
    plot_baseline_decades(baseline_decades, PLOTS_DIR / "baseline_decade_summary.png")

    print(f"Wrote required k rows to {OUTPUT_DIR / 'required_k_by_row.csv'}")
    print(f"Wrote probe rows to {OUTPUT_DIR / 'k_probe_rowwise.csv'}")
    print(f"Wrote summary to {OUTPUT_DIR / 'k_probe_summary.csv'}")
    print(f"Wrote baseline decade summary to {OUTPUT_DIR / 'baseline_decade_summary.csv'}")


if __name__ == "__main__":
    main()
