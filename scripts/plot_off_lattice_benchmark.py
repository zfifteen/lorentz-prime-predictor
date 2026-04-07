from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_CSV = REPO_ROOT / "benchmarks" / "off_lattice_benchmark.csv"
SUMMARY_JSON = REPO_ROOT / "benchmarks" / "off_lattice_benchmark_summary.json"
PLOT_DIR = REPO_ROOT / "benchmarks" / "plots" / "off_lattice"

COMPARATOR_ORDER = [
    "pnt_first_order",
    "pnt_two_term",
    "cipolla_one_over_log",
    "cipolla_one_over_log_sq",
    "li_inverse_seed",
    "axler_three_term_point_estimate",
    "lpp_seed",
]
COMPARATOR_COLORS = {
    "pnt_first_order": "#6C757D",
    "pnt_two_term": "#868E96",
    "cipolla_one_over_log": "#74C0FC",
    "cipolla_one_over_log_sq": "#339AF0",
    "li_inverse_seed": "#9775FA",
    "axler_three_term_point_estimate": "#F59F00",
    "lpp_seed": "#0B7285",
}

STAGE_EXPONENTS = {
    "baseline": range(4, 13),
    "stage_a": range(13, 15),
    "stage_b": range(15, 17),
    "stage_c": range(17, 19),
}


def _stage_name_for_exponent(exponent: int) -> str:
    for stage_name, exponents in STAGE_EXPONENTS.items():
        if exponent in exponents:
            return stage_name
    raise ValueError(f"no stage for exponent {exponent}")


def _load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with BENCHMARK_CSV.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            exponent = int(row["decade_exponent"])
            rows.append(
                {
                    "row_id": row["row_id"],
                    "stage": _stage_name_for_exponent(exponent),
                    "family": row["family"],
                    "decade_exponent": exponent,
                    "n": int(row["n"]),
                    "p_n": int(row["p_n"]),
                    "comparator": row["comparator"],
                    "seed_signed_error": int(row["seed_signed_error"]),
                    "seed_rel_ppm": float(row["seed_rel_ppm"]),
                    "refined_rel_ppm": float(row["refined_rel_ppm"]),
                }
            )
    return rows


def _load_summary() -> dict[str, object]:
    return json.loads(SUMMARY_JSON.read_text())


def _style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["figure.figsize"] = (11, 6)
    plt.rcParams["axes.titlesize"] = 15
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["legend.fontsize"] = 9


def _save(fig: plt.Figure, name: str) -> Path:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOT_DIR / name
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_stage_seed_max_ppm_by_family(summary: dict[str, object]) -> Path:
    families = summary["families"]
    stages = summary["stages"]
    fig, axes = plt.subplots(1, len(families), figsize=(6 * len(families), 6), sharey=True)
    if len(families) == 1:
        axes = [axes]
    x = np.arange(len(stages))
    for axis, family in zip(axes, families):
        for comparator in COMPARATOR_ORDER:
            values = [
                summary["by_stage"][stage]["by_family"][family]["comparators"][comparator]["seed"]["max_ppm"]
                for stage in stages
                if family in summary["by_stage"][stage]["by_family"]
            ]
            stage_positions = [
                idx for idx, stage in enumerate(stages) if family in summary["by_stage"][stage]["by_family"]
            ]
            axis.plot(
                stage_positions,
                values,
                marker="o",
                linewidth=1.8,
                color=COMPARATOR_COLORS[comparator],
                label=comparator,
            )
        axis.set_yscale("log")
        axis.set_xticks(x)
        axis.set_xticklabels(stages)
        axis.set_title(f"{family}: seed max ppm by stage")
        axis.set_xlabel("Stage")
    axes[0].set_ylabel("Seed max ppm")
    axes[-1].legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    return _save(fig, "stage_seed_max_ppm_by_family.png")


def plot_stage_seed_mean_ppm_by_family(summary: dict[str, object]) -> Path:
    families = summary["families"]
    stages = summary["stages"]
    fig, axes = plt.subplots(1, len(families), figsize=(6 * len(families), 6), sharey=True)
    if len(families) == 1:
        axes = [axes]
    x = np.arange(len(stages))
    for axis, family in zip(axes, families):
        for comparator in COMPARATOR_ORDER:
            values = [
                summary["by_stage"][stage]["by_family"][family]["comparators"][comparator]["seed"]["mean_ppm"]
                for stage in stages
                if family in summary["by_stage"][stage]["by_family"]
            ]
            stage_positions = [
                idx for idx, stage in enumerate(stages) if family in summary["by_stage"][stage]["by_family"]
            ]
            axis.plot(
                stage_positions,
                values,
                marker="o",
                linewidth=1.8,
                color=COMPARATOR_COLORS[comparator],
                label=comparator,
            )
        axis.set_yscale("log")
        axis.set_xticks(x)
        axis.set_xticklabels(stages)
        axis.set_title(f"{family}: seed mean ppm by stage")
        axis.set_xlabel("Stage")
    axes[0].set_ylabel("Seed mean ppm")
    axes[-1].legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    return _save(fig, "stage_seed_mean_ppm_by_family.png")


def plot_lpp_vs_best_classical_ratio(summary: dict[str, object]) -> Path:
    decision_cells = summary["decision"]["cells"]
    metrics = [
        ("max_ratio_lpp_to_best_classical", "Max ppm ratio"),
        ("mean_ratio_lpp_to_best_seed", "Mean ppm ratio"),
        ("median_ratio_lpp_to_best_seed", "Median ppm ratio"),
    ]
    families = sorted({cell["family"] for cell in decision_cells})
    stages = [stage for stage in summary["stages"] if stage != "baseline"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 5), sharex=True)
    for axis, (metric_key, metric_label) in zip(axes, metrics):
        for family in families:
            values = []
            for stage in stages:
                cell = next(item for item in decision_cells if item["stage"] == stage and item["family"] == family)
                values.append(float(cell[metric_key]))
            axis.plot(stages, values, marker="o", linewidth=2.0, label=family)
        axis.axhline(1.0, color="#495057", linestyle="--", linewidth=1.0)
        axis.set_yscale("log")
        axis.set_title(metric_label)
        axis.set_xlabel("Stage")
    axes[0].set_ylabel("LPP / best comparator ratio")
    axes[-1].legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    return _save(fig, "lpp_vs_best_classical_ratio.png")


def _boundary_matrix(rows: list[dict[str, object]], stage_name: str) -> tuple[np.ndarray, list[int], list[int]]:
    boundary_rows = [
        row
        for row in rows
        if row["stage"] == stage_name and row["family"] == "boundary_window" and row["comparator"] == "lpp_seed"
    ]
    decades = sorted({int(row["decade_exponent"]) for row in boundary_rows})
    offsets = sorted({int(row["n"]) - (10 ** int(row["decade_exponent"])) for row in boundary_rows})
    matrix = np.zeros((len(decades), len(offsets)))
    for i, decade in enumerate(decades):
        by_n = {
            int(row["n"]): float(row["seed_signed_error"])
            for row in boundary_rows
            if int(row["decade_exponent"]) == decade
        }
        for j, offset in enumerate(offsets):
            matrix[i, j] = by_n[(10**decade) + offset]
    return matrix, decades, offsets


def plot_boundary_window_signed_seed_error_lpp(rows: list[dict[str, object]], stage_name: str) -> Path:
    matrix, decades, offsets = _boundary_matrix(rows, stage_name)
    fig, ax = plt.subplots(figsize=(12, 5))
    image = ax.imshow(matrix, aspect="auto", cmap="coolwarm", interpolation="nearest")
    ax.set_title(f"Boundary Window Signed Seed Error: LPP ({stage_name})")
    ax.set_xlabel("Offset from decade boundary")
    ax.set_ylabel("Decade exponent")
    ax.set_xticks(np.linspace(0, len(offsets) - 1, 9))
    ax.set_xticklabels([f"{int(offsets[int(index)])}" for index in np.linspace(0, len(offsets) - 1, 9)])
    ax.set_yticks(range(len(decades)))
    ax.set_yticklabels(decades)
    fig.colorbar(image, ax=ax, label="Signed seed error")
    return _save(fig, f"boundary_window_signed_seed_error_lpp_{stage_name}.png")


def plot_dense_local_window_ranked_seed_ppm(rows: list[dict[str, object]], stage_name: str) -> Path:
    stage_rows = [row for row in rows if row["stage"] == stage_name and row["family"] == "dense_local_window"]
    fig, ax = plt.subplots(figsize=(12, 7))
    for comparator in COMPARATOR_ORDER:
        values = sorted(float(row["seed_rel_ppm"]) for row in stage_rows if row["comparator"] == comparator)
        ax.plot(
            range(1, len(values) + 1),
            values,
            marker="o",
            markersize=2,
            linewidth=1.4,
            color=COMPARATOR_COLORS[comparator],
            label=comparator,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Ranked dense local window row")
    ax.set_ylabel("Seed ppm")
    ax.set_title(f"Dense Local Window Ranked Seed ppm ({stage_name})")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    return _save(fig, f"dense_local_window_ranked_seed_ppm_{stage_name}.png")


def main() -> int:
    _style()
    rows = _load_rows()
    summary = _load_summary()
    present_stages = summary["stages"]
    outputs = [
        plot_stage_seed_max_ppm_by_family(summary),
        plot_stage_seed_mean_ppm_by_family(summary),
        plot_lpp_vs_best_classical_ratio(summary),
    ]
    for stage_name in present_stages:
        outputs.append(plot_boundary_window_signed_seed_error_lpp(rows, stage_name))
        if stage_name != "baseline":
            outputs.append(plot_dense_local_window_ranked_seed_ppm(rows, stage_name))
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
