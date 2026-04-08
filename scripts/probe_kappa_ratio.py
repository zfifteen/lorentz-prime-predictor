#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "kappa_ratio_probe"
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
            llp = gp.log(gp.log(pnt))
            basis[n] = (
                float(pnt),
                float(d_basis),
                float(k_basis),
                float(llp),
                float(math.log10(n)),
            )
    return basis


def evaluate_fixed(frame: pd.DataFrame, basis: dict[int, tuple[float, float, float, float, float]]) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []
    for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
        errors: list[float] = []
        for n, p_n in zip(group["n"], group["p_n"]):
            pnt, d_basis, k_basis, _, _ = basis[int(n)]
            estimate = math.floor(pnt + (CURRENT_C * d_basis) + (CURRENT_K * k_basis) + 0.5)
            rel_ppm = abs(estimate - int(p_n)) / int(p_n) * 1e6
            errors.append(rel_ppm)
        records.append(
            {
                "family": "fixed",
                "m": math.nan,
                "dataset": dataset_name,
                "max_rel_ppm": max(errors),
                "mean_rel_ppm": float(np.mean(errors)),
                "median_rel_ppm": float(np.median(errors)),
                "k_min": CURRENT_K,
                "k_max": CURRENT_K,
            }
        )
    return pd.DataFrame.from_records(records)


def evaluate_family(
    frame: pd.DataFrame,
    basis: dict[int, tuple[float, float, float, float, float]],
    family_name: str,
    family_fn,
    m_values: np.ndarray,
) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []
    for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
        p_n_values = group["p_n"].to_numpy(dtype=np.float64)
        pnt = np.array([basis[int(n)][0] for n in group["n"]], dtype=np.float64)
        d_basis = np.array([basis[int(n)][1] for n in group["n"]], dtype=np.float64)
        k_basis = np.array([basis[int(n)][2] for n in group["n"]], dtype=np.float64)
        llp = np.array([basis[int(n)][3] for n in group["n"]], dtype=np.float64)

        for m_value in m_values:
            k_values = family_fn(llp, float(m_value))
            estimates = np.floor(pnt + (CURRENT_C * d_basis) + (k_values * k_basis) + 0.5)
            rel_ppm = (np.abs(estimates - p_n_values) / p_n_values) * 1e6
            records.append(
                {
                    "family": family_name,
                    "m": float(m_value),
                    "dataset": dataset_name,
                    "max_rel_ppm": float(rel_ppm.max()),
                    "mean_rel_ppm": float(rel_ppm.mean()),
                    "median_rel_ppm": float(np.median(rel_ppm)),
                    "k_min": float(k_values.min()),
                    "k_max": float(k_values.max()),
                }
            )
    return pd.DataFrame.from_records(records)


def make_gated_family(dynamic_family_fn, start_log10: float, end_log10: float):
    def gated_family(llp: np.ndarray, m: float, log10_n: np.ndarray) -> np.ndarray:
        dynamic_values = dynamic_family_fn(llp, m)
        gate = np.clip((log10_n - start_log10) / (end_log10 - start_log10), 0.0, 1.0)
        return CURRENT_K + (gate * (dynamic_values - CURRENT_K))

    return gated_family


def evaluate_gated_family(
    frame: pd.DataFrame,
    basis: dict[int, tuple[float, float, float, float, float]],
    family_name: str,
    family_fn,
    m_values: np.ndarray,
) -> pd.DataFrame:
    records: list[dict[str, float | str]] = []
    for dataset_name, group in frame.groupby("dataset", sort=False, observed=False):
        p_n_values = group["p_n"].to_numpy(dtype=np.float64)
        pnt = np.array([basis[int(n)][0] for n in group["n"]], dtype=np.float64)
        d_basis = np.array([basis[int(n)][1] for n in group["n"]], dtype=np.float64)
        k_basis = np.array([basis[int(n)][2] for n in group["n"]], dtype=np.float64)
        llp = np.array([basis[int(n)][3] for n in group["n"]], dtype=np.float64)
        log10_n = np.array([basis[int(n)][4] for n in group["n"]], dtype=np.float64)

        for m_value in m_values:
            k_values = family_fn(llp, float(m_value), log10_n)
            estimates = np.floor(pnt + (CURRENT_C * d_basis) + (k_values * k_basis) + 0.5)
            rel_ppm = (np.abs(estimates - p_n_values) / p_n_values) * 1e6
            records.append(
                {
                    "family": family_name,
                    "m": float(m_value),
                    "dataset": dataset_name,
                    "max_rel_ppm": float(rel_ppm.max()),
                    "mean_rel_ppm": float(rel_ppm.mean()),
                    "median_rel_ppm": float(np.median(rel_ppm)),
                    "k_min": float(k_values.min()),
                    "k_max": float(k_values.max()),
                }
            )
    return pd.DataFrame.from_records(records)


def plot_family_sweeps(sweep: pd.DataFrame, fixed: pd.DataFrame, output_path: Path) -> None:
    families = [family for family in sweep["family"].drop_duplicates().tolist()]
    fig, axes = plt.subplots(1, len(families), figsize=(6.5 * len(families), 5.5), sharey=True)
    if len(families) == 1:
        axes = [axes]

    for ax, family in zip(axes, families):
        family_subset = sweep[sweep["family"] == family]
        for dataset_name in DATASET_ORDER:
            subset = family_subset[family_subset["dataset"] == dataset_name].sort_values("m")
            ax.plot(
                subset["m"],
                subset["max_rel_ppm"],
                linewidth=2,
                color=DATASET_COLORS[dataset_name],
                label=DATASET_LABELS[dataset_name],
            )
            fixed_value = float(
                fixed[(fixed["dataset"] == dataset_name) & (fixed["family"] == "fixed")]["max_rel_ppm"].iloc[0]
            )
            ax.axhline(
                fixed_value,
                color=DATASET_COLORS[dataset_name],
                linestyle="--",
                linewidth=1,
                alpha=0.55,
            )
        ax.set_title(f"{family}: max seed ppm vs ratio scale")
        ax.set_xlabel("m")
        ax.grid(True, alpha=0.25)

    axes[0].set_ylabel("max seed ppm")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_tradeoff_frontier(sweep: pd.DataFrame, fixed: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), sharex=False, sharey=False)
    pairings = [
        ("reproducible_exact_baseline", "reproducible_exact_stage_b"),
        ("published_exact_grid_ge_1e4", "reproducible_exact_stage_b"),
        ("reproducible_exact_stage_a", "reproducible_exact_stage_b"),
    ]

    for ax, (x_dataset, y_dataset) in zip(axes, pairings):
        for family in sweep["family"].drop_duplicates().tolist():
            pivot = (
                sweep[sweep["family"] == family]
                .pivot(index="m", columns="dataset", values="max_rel_ppm")
                .reset_index()
                .sort_values("m")
            )
            ax.plot(
                pivot[x_dataset],
                pivot[y_dataset],
                linewidth=2,
                label=family,
            )
            best_idx = pivot[y_dataset].idxmin()
            ax.scatter(
                pivot.loc[best_idx, x_dataset],
                pivot.loc[best_idx, y_dataset],
                s=45,
            )

        fixed_x = float(fixed[fixed["dataset"] == x_dataset]["max_rel_ppm"].iloc[0])
        fixed_y = float(fixed[fixed["dataset"] == y_dataset]["max_rel_ppm"].iloc[0])
        ax.scatter(fixed_x, fixed_y, color="black", s=70, marker="x", label="fixed 0.065")
        ax.set_xlabel(f"{DATASET_LABELS[x_dataset]} max ppm")
        ax.set_ylabel(f"{DATASET_LABELS[y_dataset]} max ppm")
        ax.grid(True, alpha=0.25)

    handles, labels = axes[0].get_legend_handles_labels()
    dedup: dict[str, object] = {}
    for handle, label in zip(handles, labels):
        dedup[label] = handle
    fig.legend(dedup.values(), dedup.keys(), loc="upper center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_k_curves(
    basis: dict[int, tuple[float, float, float, float, float]],
    output_path: Path,
) -> None:
    sample_keys = sorted(basis.keys())
    sample_log10 = np.array([basis[n][4] for n in sample_keys], dtype=np.float64)
    llp = np.array([basis[n][3] for n in sample_keys], dtype=np.float64)
    gate_end_8 = np.clip((sample_log10 - 5.0) / 3.0, 0.0, 1.0)
    gate_end_12 = np.clip((sample_log10 - 5.0) / 7.0, 0.0, 1.0)
    dynamic_sq = (llp**2) / (10.0 * math.e**2)

    curves = [
        ("fixed 0.065", np.full_like(sample_log10, CURRENT_K), "#111111"),
        ("llp/(5e^2)", llp / (5.0 * math.e**2), "#1f77b4"),
        ("llp^2/(10e^2)", (llp**2) / (10.0 * math.e**2), "#2ca02c"),
        (
            "gated llp^2/(10e^2), full by 1e8",
            CURRENT_K + (gate_end_8 * (dynamic_sq - CURRENT_K)),
            "#d62728",
        ),
        (
            "gated llp^2/(10e^2), full by 1e12",
            CURRENT_K + (gate_end_12 * (dynamic_sq - CURRENT_K)),
            "#9467bd",
        ),
    ]

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    for label, values, color in curves:
        ax.plot(sample_log10, values, linewidth=2, label=label, color=color)
    ax.set_title("k* ratio curves across the exact benchmark scales")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("k*")
    ax.grid(True, alpha=0.25)
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
    frame["dataset"] = pd.Categorical(frame["dataset"], categories=DATASET_ORDER, ordered=True)
    frame = frame.sort_values(["dataset", "n"]).reset_index(drop=True)

    basis = compute_basis(sorted(frame["n"].unique().tolist()))
    fixed = evaluate_fixed(frame, basis)

    family_configs = [
        ("llp_over_me2", lambda llp, m: llp / (m * math.e**2)),
        ("llp_sq_over_me2", lambda llp, m: (llp**2) / (m * math.e**2)),
    ]
    gated_family_configs = [
        (
            "gated_llp_sq_over_me2_end8",
            make_gated_family(lambda llp, m: (llp**2) / (m * math.e**2), 5.0, 8.0),
        ),
        (
            "gated_llp_sq_over_me2_end12",
            make_gated_family(lambda llp, m: (llp**2) / (m * math.e**2), 5.0, 12.0),
        ),
    ]
    m_values = np.linspace(5.0, 60.0, 221)

    sweep_frames = [evaluate_family(frame, basis, name, fn, m_values) for name, fn in family_configs]
    sweep_frames.extend(
        [evaluate_gated_family(frame, basis, name, fn, m_values) for name, fn in gated_family_configs]
    )
    sweep = pd.concat(sweep_frames, ignore_index=True)
    combined = pd.concat([fixed, sweep], ignore_index=True)

    best_rows = (
        sweep.sort_values(["family", "dataset", "max_rel_ppm"])
        .groupby(["family", "dataset"], as_index=False)
        .first()
    )

    combined.to_csv(OUTPUT_DIR / "ratio_family_sweep.csv", index=False, lineterminator="\n")
    best_rows.to_csv(OUTPUT_DIR / "ratio_family_best_points.csv", index=False, lineterminator="\n")

    plot_family_sweeps(sweep, fixed, PLOTS_DIR / "ratio_family_sweeps.png")
    plot_tradeoff_frontier(sweep, fixed, PLOTS_DIR / "ratio_tradeoff_frontier.png")
    plot_k_curves(basis, PLOTS_DIR / "ratio_k_curves.png")

    print(f"Wrote sweep to {OUTPUT_DIR / 'ratio_family_sweep.csv'}")
    print(f"Wrote best points to {OUTPUT_DIR / 'ratio_family_best_points.csv'}")


if __name__ == "__main__":
    main()
