#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "constant_probe"
PLOTS_DIR = OUTPUT_DIR / "plots"

CURRENT_C = -0.00016667
CURRENT_K = 0.06500
ARCHIVE_BASELINE_C = -0.00247
ARCHIVE_BASELINE_K = 0.04449


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
            rows.append(("published_exact_grid", n, p_n))
    return rows


def load_exact_csv(path: Path, dataset_name: str) -> list[tuple[str, int, int]]:
    rows: list[tuple[str, int, int]] = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append((dataset_name, int(row["n"]), int(row["p_n"])))
    return rows


def compute_basis(unique_n: list[int]) -> dict[int, tuple[float, float, float]]:
    basis: dict[int, tuple[float, float, float]] = {}
    for n in unique_n:
        if n < 2:
            basis[n] = (2.0, 0.0, 0.0)
            continue
        precision = max(256, int(gp.log2(n)) + 256)
        with gp.local_context(gp.context(), precision=precision):
            n_mp = gp.mpfr(n)
            ln_n = gp.log(n_mp)
            ln_ln_n = gp.log(ln_n)
            pnt = n_mp * (ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n))
            if pnt <= 0:
                pnt = n_mp
            e_fourth = gp.exp(gp.mpfr(4))
            d_basis = pnt * ((gp.log(pnt) / e_fourth) ** 2)
            k_basis = pnt ** gp.mpfr("0.6666666666666666")
            basis[n] = (float(pnt), float(d_basis), float(k_basis))
    return basis


def evaluate_config(
    frame: pd.DataFrame,
    basis: dict[int, tuple[float, float, float]],
    c_value: float,
    k_value: float,
) -> pd.DataFrame:
    pnt = np.array([basis[n][0] for n in frame["n"]], dtype=np.float64)
    d_basis = np.array([basis[n][1] for n in frame["n"]], dtype=np.float64)
    k_basis = np.array([basis[n][2] for n in frame["n"]], dtype=np.float64)
    estimates = np.floor(pnt + (c_value * d_basis) + (k_value * k_basis) + 0.5)
    abs_error = np.abs(estimates - frame["p_n"].to_numpy(dtype=np.float64))
    rel_ppm = (abs_error / frame["p_n"].to_numpy(dtype=np.float64)) * 1e6
    return pd.DataFrame(
        {
            "dataset": frame["dataset"].to_numpy(),
            "n": frame["n"].to_numpy(),
            "p_n": frame["p_n"].to_numpy(),
            "estimate": estimates,
            "abs_error": abs_error,
            "rel_ppm": rel_ppm,
        }
    )


def summarize_config(name: str, c_value: float, k_value: float, evaluated: pd.DataFrame) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for dataset_name, group in evaluated.groupby("dataset", sort=False):
        rows.append(
            {
                "config": name,
                "dataset": dataset_name,
                "c": c_value,
                "kappa_star": k_value,
                "max_rel_ppm": float(group["rel_ppm"].max()),
                "mean_rel_ppm": float(group["rel_ppm"].mean()),
                "median_rel_ppm": float(group["rel_ppm"].median()),
            }
        )
    return rows


def build_heatmap(
    frame: pd.DataFrame,
    basis: dict[int, tuple[float, float, float]],
    dataset_name: str,
    c_values: np.ndarray,
    k_values: np.ndarray,
) -> pd.DataFrame:
    subset = frame[frame["dataset"] == dataset_name].reset_index(drop=True)
    pnt = np.array([basis[n][0] for n in subset["n"]], dtype=np.float64)
    d_basis = np.array([basis[n][1] for n in subset["n"]], dtype=np.float64)
    k_basis = np.array([basis[n][2] for n in subset["n"]], dtype=np.float64)
    p_n = subset["p_n"].to_numpy(dtype=np.float64)
    records: list[dict[str, float | str]] = []
    for c_value in c_values:
        estimates_by_k = np.floor(
            pnt[np.newaxis, :]
            + (c_value * d_basis[np.newaxis, :])
            + (k_values[:, np.newaxis] * k_basis[np.newaxis, :])
            + 0.5
        )
        rel_ppm = (np.abs(estimates_by_k - p_n[np.newaxis, :]) / p_n[np.newaxis, :]) * 1e6
        max_rel = rel_ppm.max(axis=1)
        mean_rel = rel_ppm.mean(axis=1)
        for k_value, max_value, mean_value in zip(k_values, max_rel, mean_rel):
            records.append(
                {
                    "dataset": dataset_name,
                    "c": float(c_value),
                    "kappa_star": float(k_value),
                    "max_rel_ppm": float(max_value),
                    "mean_rel_ppm": float(mean_value),
                }
            )
    return pd.DataFrame.from_records(records)


def plot_heatmap(surface: pd.DataFrame, dataset_name: str, output_path: Path) -> None:
    pivot = surface.pivot(index="kappa_star", columns="c", values="max_rel_ppm").sort_index(ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    image = ax.imshow(pivot.to_numpy(), aspect="auto", origin="lower", cmap="magma")
    ax.set_title(f"Max seed ppm on {dataset_name}")
    ax.set_xlabel("c")
    ax.set_ylabel("k*")
    x_positions = np.linspace(0, len(pivot.columns) - 1, min(6, len(pivot.columns))).astype(int)
    y_positions = np.linspace(0, len(pivot.index) - 1, min(6, len(pivot.index))).astype(int)
    ax.set_xticks(x_positions, [f"{pivot.columns[i]:.5f}" for i in x_positions], rotation=45, ha="right")
    ax.set_yticks(y_positions, [f"{pivot.index[i]:.3f}" for i in y_positions])
    historical_points = [
        (CURRENT_C, CURRENT_K, "current"),
        (ARCHIVE_BASELINE_C, ARCHIVE_BASELINE_K, "archive baseline"),
        (CURRENT_C, 0.045, "k*=0.045"),
        (CURRENT_C, 0.03, "k*=0.03"),
    ]
    for c_value, k_value, label in historical_points:
        if c_value < pivot.columns.min() or c_value > pivot.columns.max():
            continue
        if k_value < pivot.index.min() or k_value > pivot.index.max():
            continue
        c_idx = float(np.interp(c_value, pivot.columns.to_numpy(), np.arange(len(pivot.columns))))
        k_idx = float(np.interp(k_value, pivot.index.to_numpy(), np.arange(len(pivot.index))))
        ax.scatter(c_idx, k_idx, s=60, facecolors="none", edgecolors="cyan")
        ax.text(c_idx + 0.2, k_idx + 0.2, label, color="white", fontsize=8)
    fig.colorbar(image, ax=ax, label="max relative error (ppm)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_kappa_history(summary: pd.DataFrame, output_path: Path) -> None:
    plot_rows = summary[summary["dataset"] == "reproducible_exact_all"].copy()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(plot_rows["kappa_star"], plot_rows["max_rel_ppm"], marker="o", linewidth=2, color="#1f77b4")
    for _, row in plot_rows.iterrows():
        label = row["config"].replace("_", " ")
        ax.annotate(label, (row["kappa_star"], row["max_rel_ppm"]), textcoords="offset points", xytext=(4, 4), fontsize=8)
    ax.set_title("Historical k* probe on reproducible exact data")
    ax.set_xlabel("k*")
    ax.set_ylabel("max seed ppm")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_c_probe(surface: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    for dataset_name, color in [
        ("published_exact_grid_ge_1e4", "#d62728"),
        ("reproducible_exact_all", "#2ca02c"),
    ]:
        subset = surface[(surface["dataset"] == dataset_name) & (surface["kappa_star"].round(5) == 0.06500)].sort_values("c")
        ax.plot(subset["c"], subset["max_rel_ppm"], linewidth=2, label=dataset_name, color=color)
    ax.axvline(CURRENT_C, color="black", linestyle="--", linewidth=1, label="current c")
    ax.set_title("Max seed ppm versus c at k* = 0.065")
    ax.set_xlabel("c")
    ax.set_ylabel("max seed ppm")
    ax.grid(True, alpha=0.3)
    ax.legend()
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
    published_large = frame[(frame["dataset"] == "published_exact_grid") & (frame["n"] >= 10_000)].copy()
    published_large["dataset"] = "published_exact_grid_ge_1e4"
    reproducible_all = frame[frame["dataset"].str.startswith("reproducible_exact_")].copy()
    reproducible_all["dataset"] = "reproducible_exact_all"
    frame = pd.concat([frame, published_large, reproducible_all], ignore_index=True)

    unique_n = sorted(frame["n"].unique().tolist())
    basis = compute_basis(unique_n)

    configs = [
        ("kappa_0_030_current_c", CURRENT_C, 0.03),
        ("archive_baseline_pair", ARCHIVE_BASELINE_C, ARCHIVE_BASELINE_K),
        ("kappa_0_045_current_c", CURRENT_C, 0.045),
        ("archive_baseline_k_current_c", CURRENT_C, ARCHIVE_BASELINE_K),
        ("current_pair", CURRENT_C, CURRENT_K),
    ]

    summary_rows: list[dict[str, float | str]] = []
    for name, c_value, k_value in configs:
        evaluated = evaluate_config(frame, basis, c_value, k_value)
        summary_rows.extend(summarize_config(name, c_value, k_value, evaluated))

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUTPUT_DIR / "historical_constant_summary.csv", index=False, lineterminator="\n")

    c_values = np.linspace(-0.0030, 0.0006, 37)
    k_values = np.linspace(0.02, 0.08, 49)
    published_surface = build_heatmap(frame, basis, "published_exact_grid_ge_1e4", c_values, k_values)
    reproducible_surface = build_heatmap(frame, basis, "reproducible_exact_all", c_values, k_values)
    surface = pd.concat([published_surface, reproducible_surface], ignore_index=True)
    surface.to_csv(OUTPUT_DIR / "constant_surface.csv", index=False, lineterminator="\n")

    plot_heatmap(
        published_surface,
        "published exact grid (n >= 10^4)",
        PLOTS_DIR / "published_exact_grid_ge_1e4_max_ppm_heatmap.png",
    )
    plot_heatmap(
        reproducible_surface,
        "reproducible exact all",
        PLOTS_DIR / "reproducible_exact_all_max_ppm_heatmap.png",
    )

    history_subset = summary[
        (summary["dataset"] == "reproducible_exact_all")
        & (summary["config"].isin(["kappa_0_030_current_c", "kappa_0_045_current_c", "archive_baseline_k_current_c", "current_pair"]))
    ].sort_values("kappa_star")
    plot_kappa_history(history_subset, PLOTS_DIR / "kappa_history_probe.png")
    plot_c_probe(surface, PLOTS_DIR / "c_probe_at_kappa_0_065.png")

    best_rows = surface.sort_values(["dataset", "max_rel_ppm"]).groupby("dataset", as_index=False).first()
    best_rows.to_csv(OUTPUT_DIR / "best_surface_points.csv", index=False, lineterminator="\n")

    print(f"Wrote summary to {OUTPUT_DIR / 'historical_constant_summary.csv'}")
    print(f"Wrote surface to {OUTPUT_DIR / 'constant_surface.csv'}")
    print(f"Wrote best points to {OUTPUT_DIR / 'best_surface_points.csv'}")


if __name__ == "__main__":
    main()
