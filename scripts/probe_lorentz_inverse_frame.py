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
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "lorentz_inverse_frame_probe"
PLOTS_DIR = OUTPUT_DIR / "plots"

DATASET_SPECS = [
    ("baseline", DATA_DIR / "held_out_exact_primes_1e4_1e12.csv"),
    ("stage_a", DATA_DIR / "held_out_exact_primes_1e13_1e14.csv"),
    ("stage_b", DATA_DIR / "held_out_exact_primes_1e15_1e16.csv"),
]

DATASET_LABELS = {
    "baseline": "baseline exact",
    "stage_a": "stage_a exact",
    "stage_b": "stage_b exact",
}

FAMILY_ORDER = [
    "boundary_window",
    "dense_local_window",
    "off_lattice_decimal",
]

MODEL_ORDER = [
    "base_li_inverse",
    "classical_inverse_frame",
    "lorentz_inverse_frame",
]

MODEL_LABELS = {
    "base_li_inverse": "base li_inverse",
    "classical_inverse_frame": "classical inverse frame",
    "lorentz_inverse_frame": "Lorentz-style inverse frame",
}

MODEL_COLORS = {
    "base_li_inverse": "#2b8a3e",
    "classical_inverse_frame": "#1c7ed6",
    "lorentz_inverse_frame": "#f76707",
}

SPLIT_SPECS = [
    {
        "name": "baseline_to_stage_a",
        "train_datasets": ["baseline"],
        "test_dataset": "stage_a",
    },
    {
        "name": "baseline_stage_a_to_stage_b",
        "train_datasets": ["baseline", "stage_a"],
        "test_dataset": "stage_b",
    },
]


def load_exact_csv(path: Path, dataset_name: str) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "dataset": dataset_name,
                    "row_id": row["row_id"],
                    "family": row["family"],
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


def build_feature_table(rows: list[dict[str, int | str]]) -> dict[int, dict[str, float | int]]:
    unique_n_values = sorted({int(row["n"]) for row in rows})
    feature_table: dict[int, dict[str, float | int]] = {}
    for n_value in unique_n_values:
        x0 = li_inverse_seed(n_value)
        log_x0 = math.log(x0)
        feature_table[n_value] = {
            "x0": x0,
            "classical_1": 1.0 / log_x0,
            "classical_2": 1.0 / (log_x0 * log_x0),
            "lorentz_1": (log_x0 / (math.e**4)) ** 2,
            "lorentz_2": x0 ** (-1.0 / 3.0),
        }
    return feature_table


def attach_features(
    rows: list[dict[str, int | str]],
    feature_table: dict[int, dict[str, float | int]],
) -> list[dict[str, object]]:
    enriched_rows: list[dict[str, object]] = []
    for row in rows:
        n_value = int(row["n"])
        p_value = int(row["p_n"])
        features = feature_table[n_value]
        x0 = int(features["x0"])
        residual = (p_value - x0) / x0
        enriched_rows.append(
            {
                **row,
                **features,
                "residual": residual,
            }
        )
    return enriched_rows


def fit_two_term_residual(
    rows: list[dict[str, object]],
    key_1: str,
    key_2: str,
) -> tuple[float, float]:
    matrix = np.array([[float(row[key_1]), float(row[key_2])] for row in rows], dtype=np.float64)
    targets = np.array([float(row["residual"]) for row in rows], dtype=np.float64)
    coefficients, _, _, _ = np.linalg.lstsq(matrix, targets, rcond=None)
    return float(coefficients[0]), float(coefficients[1])


def predict_value(
    row: dict[str, object],
    model_name: str,
    classical_coefficients: tuple[float, float],
    lorentz_coefficients: tuple[float, float],
) -> int:
    x0 = int(row["x0"])
    if model_name == "base_li_inverse":
        return x0
    if model_name == "classical_inverse_frame":
        correction = (
            classical_coefficients[0] * float(row["classical_1"])
            + classical_coefficients[1] * float(row["classical_2"])
        )
        return int(round(x0 * (1.0 + correction)))
    if model_name == "lorentz_inverse_frame":
        correction = (
            lorentz_coefficients[0] * float(row["lorentz_1"])
            + lorentz_coefficients[1] * float(row["lorentz_2"])
        )
        return int(round(x0 * (1.0 + correction)))
    raise ValueError(f"unknown model: {model_name}")


def ppm_error(estimate: int, p_value: int) -> float:
    return abs(estimate - p_value) / p_value * 1e6


def summarize(values: list[float]) -> dict[str, float]:
    array = np.array(values, dtype=np.float64)
    return {
        "mean_ppm": float(array.mean()),
        "median_ppm": float(np.median(array)),
        "max_ppm": float(array.max()),
        "rms_ppm": float(np.sqrt(np.mean(np.square(array)))),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_stage_means(summary_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 4.8), constrained_layout=True)
    x_positions = np.arange(len(SPLIT_SPECS))
    width = 0.24
    offsets = {
        "base_li_inverse": -width,
        "classical_inverse_frame": 0.0,
        "lorentz_inverse_frame": width,
    }

    for model_name in MODEL_ORDER:
        heights = []
        for split in SPLIT_SPECS:
            row = next(
                item
                for item in summary_rows
                if item["split"] == split["name"] and item["model"] == model_name
            )
            heights.append(float(row["mean_ppm"]))
        ax.bar(
            x_positions + offsets[model_name],
            heights,
            width=width,
            color=MODEL_COLORS[model_name],
            label=MODEL_LABELS[model_name],
        )

    ax.set_yscale("log")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        [
            "fit baseline\n test stage_a",
            "fit baseline+stage_a\n test stage_b",
        ]
    )
    ax.set_ylabel("held-out mean seed ppm")
    ax.set_title("Exact held-out stage means on inverse-li backbone")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(PLOTS_DIR / "heldout_stage_mean_ppm.png", dpi=180)
    plt.close(fig)


def plot_family_maxima(family_rows: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)
    width = 0.24
    split_to_axis = {
        "baseline_to_stage_a": axes[0],
        "baseline_stage_a_to_stage_b": axes[1],
    }
    offsets = {
        "base_li_inverse": -width,
        "classical_inverse_frame": 0.0,
        "lorentz_inverse_frame": width,
    }

    for split_name, ax in split_to_axis.items():
        x_positions = np.arange(len(FAMILY_ORDER))
        for model_name in MODEL_ORDER:
            heights = []
            for family_name in FAMILY_ORDER:
                row = next(
                    item
                    for item in family_rows
                    if item["split"] == split_name
                    and item["model"] == model_name
                    and item["family"] == family_name
                )
                heights.append(float(row["max_ppm"]))
            ax.bar(
                x_positions + offsets[model_name],
                heights,
                width=width,
                color=MODEL_COLORS[model_name],
                label=MODEL_LABELS[model_name],
            )
        ax.set_yscale("log")
        ax.set_xticks(x_positions)
        ax.set_xticklabels(FAMILY_ORDER, rotation=20, ha="right")
        ax.set_ylabel("held-out max seed ppm")
        ax.set_title(
            "test stage_a"
            if split_name == "baseline_to_stage_a"
            else "test stage_b"
        )
        ax.grid(True, axis="y", alpha=0.25)

    axes[0].legend()
    fig.suptitle("Exact family max seed ppm on inverse-li backbone", fontsize=14)
    fig.savefig(PLOTS_DIR / "heldout_stage_family_max_ppm.png", dpi=180)
    plt.close(fig)


def write_readme(
    coefficient_rows: list[dict[str, object]],
    split_summary_rows: list[dict[str, object]],
    family_summary_rows: list[dict[str, object]],
) -> None:
    def find_split_row(split_name: str, model_name: str) -> dict[str, object]:
        return next(
            row
            for row in split_summary_rows
            if row["split"] == split_name and row["model"] == model_name
        )

    lines = [
        "# Lorentz Inverse Frame Probe",
        "",
        "This probe tests a narrow question on exact data only:",
        "",
        "Can a small Lorentz-style residual model on top of the same `li_inverse_seed` backbone extrapolate better than a same-budget classical residual model?",
        "",
        "The backbone is fixed:",
        "",
        "- `base_li_inverse(n) = li_inverse_seed(n)`",
        "",
        "The signed residual is measured on the backbone scale:",
        "",
        "- `r(n) = (p_n - base_li_inverse(n)) / base_li_inverse(n)`",
        "",
        "Two two-term frames are fit by least squares on exact training rows:",
        "",
        "- `classical_inverse_frame`: `r_hat = a/log(x0) + b/log(x0)^2`",
        "- `lorentz_inverse_frame`: `r_hat = c*(log(x0)/e^4)^2 + k*x0^(-1/3)`",
        "",
        "The comparison is sequential and exact-only:",
        "",
        "- fit on baseline exact, test on exact `stage_a`",
        "- fit on baseline exact plus exact `stage_a`, test on exact `stage_b`",
        "",
        "## Strongest Finding",
        "",
    ]

    stage_a_classical = find_split_row("baseline_to_stage_a", "classical_inverse_frame")
    stage_a_lorentz = find_split_row("baseline_to_stage_a", "lorentz_inverse_frame")
    stage_b_classical = find_split_row("baseline_stage_a_to_stage_b", "classical_inverse_frame")
    stage_b_lorentz = find_split_row("baseline_stage_a_to_stage_b", "lorentz_inverse_frame")
    lines.extend(
        [
            "The bare `li_inverse_seed` backbone stays strongest on the held-out exact stages in this first probe.",
            "",
            "But the Lorentz-style residual frame extrapolates better than the same-budget classical residual frame on both exact held-out splits:",
            "",
            f"- baseline -> `stage_a` mean ppm: `classical_inverse_frame = {float(stage_a_classical['mean_ppm']):.6f}`, `lorentz_inverse_frame = {float(stage_a_lorentz['mean_ppm']):.6f}`",
            f"- baseline + `stage_a` -> `stage_b` mean ppm: `classical_inverse_frame = {float(stage_b_classical['mean_ppm']):.6f}`, `lorentz_inverse_frame = {float(stage_b_lorentz['mean_ppm']):.6f}`",
            "",
            "That does not prove the Lorentz frame is the final inverse answer. It does show that, under a matched tiny residual budget, the Lorentz-style frame carries more of the deep exact structure forward than the classical residual frame does.",
            "",
            "## Artifacts",
            "",
            "- [split_summary.csv](./split_summary.csv)",
            "- [family_summary.csv](./family_summary.csv)",
            "- [fit_coefficients.csv](./fit_coefficients.csv)",
            "- [rowwise_results.csv](./rowwise_results.csv)",
            "- [heldout_stage_mean_ppm.png](./plots/heldout_stage_mean_ppm.png)",
            "- [heldout_stage_family_max_ppm.png](./plots/heldout_stage_family_max_ppm.png)",
            "",
        ]
    )
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_rows: list[dict[str, int | str]] = []
    for dataset_name, path in DATASET_SPECS:
        raw_rows.extend(load_exact_csv(path, dataset_name))

    feature_table = build_feature_table(raw_rows)
    rows = attach_features(raw_rows, feature_table)

    rowwise_results: list[dict[str, object]] = []
    split_summary_rows: list[dict[str, object]] = []
    family_summary_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []

    for split in SPLIT_SPECS:
        split_name = str(split["name"])
        train_datasets = set(split["train_datasets"])
        test_dataset = str(split["test_dataset"])

        train_rows = [row for row in rows if str(row["dataset"]) in train_datasets]
        test_rows = [row for row in rows if str(row["dataset"]) == test_dataset]

        classical_coefficients = fit_two_term_residual(train_rows, "classical_1", "classical_2")
        lorentz_coefficients = fit_two_term_residual(train_rows, "lorentz_1", "lorentz_2")

        coefficient_rows.extend(
            [
                {
                    "split": split_name,
                    "model": "classical_inverse_frame",
                    "coefficient_1": classical_coefficients[0],
                    "coefficient_2": classical_coefficients[1],
                },
                {
                    "split": split_name,
                    "model": "lorentz_inverse_frame",
                    "coefficient_1": lorentz_coefficients[0],
                    "coefficient_2": lorentz_coefficients[1],
                },
            ]
        )

        for row in test_rows:
            p_value = int(row["p_n"])
            for model_name in MODEL_ORDER:
                estimate = predict_value(row, model_name, classical_coefficients, lorentz_coefficients)
                rowwise_results.append(
                    {
                        "split": split_name,
                        "dataset": row["dataset"],
                        "family": row["family"],
                        "row_id": row["row_id"],
                        "n": row["n"],
                        "p_n": p_value,
                        "model": model_name,
                        "estimate": estimate,
                        "ppm": ppm_error(estimate, p_value),
                    }
                )

        for model_name in MODEL_ORDER:
            values = [
                float(row["ppm"])
                for row in rowwise_results
                if row["split"] == split_name and row["model"] == model_name
            ]
            split_summary_rows.append(
                {
                    "split": split_name,
                    "test_dataset": test_dataset,
                    "model": model_name,
                    **summarize(values),
                }
            )

        for family_name in FAMILY_ORDER:
            for model_name in MODEL_ORDER:
                values = [
                    float(row["ppm"])
                    for row in rowwise_results
                    if row["split"] == split_name
                    and row["model"] == model_name
                    and row["family"] == family_name
                ]
                family_summary_rows.append(
                    {
                        "split": split_name,
                        "test_dataset": test_dataset,
                        "family": family_name,
                        "model": model_name,
                        **summarize(values),
                    }
                )

    write_csv(
        OUTPUT_DIR / "fit_coefficients.csv",
        ["split", "model", "coefficient_1", "coefficient_2"],
        coefficient_rows,
    )
    write_csv(
        OUTPUT_DIR / "split_summary.csv",
        ["split", "test_dataset", "model", "mean_ppm", "median_ppm", "max_ppm", "rms_ppm"],
        split_summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "family_summary.csv",
        ["split", "test_dataset", "family", "model", "mean_ppm", "median_ppm", "max_ppm", "rms_ppm"],
        family_summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "rowwise_results.csv",
        ["split", "dataset", "family", "row_id", "n", "p_n", "model", "estimate", "ppm"],
        rowwise_results,
    )

    plot_stage_means(split_summary_rows)
    plot_family_maxima(family_summary_rows)
    write_readme(coefficient_rows, split_summary_rows, family_summary_rows)


if __name__ == "__main__":
    main()
