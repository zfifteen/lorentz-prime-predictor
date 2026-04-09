#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "benchmarks" / "gwr_hybrid_probe" / "rowwise_results.csv"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "gwr_bracket_regions"
PLOTS_DIR = OUTPUT_DIR / "plots"

TARGET_VARIANT = "r_inverse_seed"
TARGET_FAMILIES = {"boundary_window", "dense_local_window", "published_exact_grid"}

ZONE_ORDER = ["other", "mant_0.5", "mant_0.9", "mant_1.0"]
ZONE_COLORS = {
    "other": "#495057",
    "mant_0.5": "#0b7285",
    "mant_0.9": "#c92a2a",
    "mant_1.0": "#6741d9",
}
ZONE_LABELS = {
    "other": "other",
    "mant_0.5": "mantissa ~0.5",
    "mant_0.9": "mantissa ~0.9",
    "mant_1.0": "mantissa ~1.0",
}


def major_zone(n_value: int, decade_exponent: int) -> str:
    mantissa = n_value / (10**decade_exponent)
    if 0.49 <= mantissa <= 0.51:
        return "mant_0.5"
    if 0.89 <= mantissa <= 0.91:
        return "mant_0.9"
    if 0.999 <= mantissa <= 1.0011:
        return "mant_1.0"
    return "other"


def percentile(values: list[int], pct: float) -> int:
    if not values:
        raise ValueError("values must be non-empty")
    return int(np.percentile(np.array(values, dtype=float), pct))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_offset_brackets(summary_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots(figsize=(11.0, 5.8))
    for zone_name in ZONE_ORDER:
        zone_rows = [row for row in summary_rows if row["zone"] == zone_name]
        if not zone_rows:
            continue
        xs = np.array([int(row["decade_exponent"]) for row in zone_rows], dtype=float)
        centers = np.array([int(row["median_offset"]) for row in zone_rows], dtype=float)
        lowers = np.array([int(row["min_offset"]) for row in zone_rows], dtype=float)
        uppers = np.array([int(row["max_offset"]) for row in zone_rows], dtype=float)
        yerr = np.vstack((centers - lowers, uppers - centers))
        ax.errorbar(
            xs,
            centers,
            yerr=yerr,
            fmt="o",
            color=ZONE_COLORS[zone_name],
            linewidth=2,
            capsize=4,
            label=ZONE_LABELS[zone_name],
        )
    ax.axhline(0.0, color="#adb5bd", linewidth=1)
    ax.set_xlabel("Decade exponent of n")
    ax.set_ylabel("r_inverse_seed(n) - true witness")
    ax.set_title("Exact witness offset bands for r_inverse_seed by decade and coarse mantissa zone")
    ax.set_yscale("symlog", linthresh=1000)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "r_inverse_offset_brackets.png", dpi=200)
    plt.close(fig)


def plot_radius_comparison(summary_rows: list[dict[str, object]], global_radius: int) -> None:
    rows = [row for row in summary_rows if row["row_count"] >= 200]
    labels = [f"{row['decade_exponent']}:{row['zone']}" for row in rows]
    radii = [int(row["max_centered_radius"]) for row in rows]

    fig, ax = plt.subplots(figsize=(12.5, 5.4))
    positions = np.arange(len(rows))
    ax.bar(positions, radii, color="#0b7285")
    ax.axhline(global_radius, color="#c92a2a", linewidth=2, label=f"single global radius = {global_radius:,}")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("Radius needed for exact witness coverage")
    ax.set_title("Class-conditioned witness brackets are far tighter than one global exact radius")
    ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "class_radius_vs_global.png", dpi=200)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    with INPUT_PATH.open(newline="") as handle:
        all_rows = list(csv.DictReader(handle))

    rows = [
        row
        for row in all_rows
        if row["variant"] == TARGET_VARIANT and row["family"] in TARGET_FAMILIES
    ]

    global_offsets = [int(row["seed_minus_winner"]) for row in rows]
    global_radius = max(abs(value) for value in global_offsets)
    global_width = max(global_offsets) - min(global_offsets)

    grouped: dict[tuple[int, str], list[int]] = defaultdict(list)
    for row in rows:
        decade_exponent = int(row["decade_exponent"])
        zone_name = major_zone(int(row["n"]), decade_exponent)
        grouped[(decade_exponent, zone_name)].append(int(row["seed_minus_winner"]))

    summary_rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        decade_exponent, zone_name = key
        offsets = sorted(grouped[key])
        center = int(np.median(np.array(offsets, dtype=float)))
        radius = max(abs(value - center) for value in offsets)
        summary_rows.append(
            {
                "decade_exponent": decade_exponent,
                "zone": zone_name,
                "row_count": len(offsets),
                "min_offset": offsets[0],
                "p05_offset": percentile(offsets, 5),
                "median_offset": center,
                "p95_offset": percentile(offsets, 95),
                "max_offset": offsets[-1],
                "bracket_width": offsets[-1] - offsets[0],
                "max_centered_radius": radius,
            }
        )

    global_comparison = [
        {
            "variant": TARGET_VARIANT,
            "row_count": len(rows),
            "global_min_offset": min(global_offsets),
            "global_max_offset": max(global_offsets),
            "global_exact_width": global_width,
            "global_exact_radius": global_radius,
            "median_class_exact_width": int(np.median([int(row["bracket_width"]) for row in summary_rows])),
            "max_class_exact_width": max(int(row["bracket_width"]) for row in summary_rows),
            "median_class_centered_radius": int(np.median([int(row["max_centered_radius"]) for row in summary_rows])),
            "max_class_centered_radius": max(int(row["max_centered_radius"]) for row in summary_rows),
        }
    ]

    write_csv(
        OUTPUT_DIR / "zone_bracket_summary.csv",
        [
            "decade_exponent",
            "zone",
            "row_count",
            "min_offset",
            "p05_offset",
            "median_offset",
            "p95_offset",
            "max_offset",
            "bracket_width",
            "max_centered_radius",
        ],
        summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "global_comparison.csv",
        [
            "variant",
            "row_count",
            "global_min_offset",
            "global_max_offset",
            "global_exact_width",
            "global_exact_radius",
            "median_class_exact_width",
            "max_class_exact_width",
            "median_class_centered_radius",
            "max_class_centered_radius",
        ],
        global_comparison,
    )

    plot_offset_brackets(summary_rows)
    plot_radius_comparison(summary_rows, global_radius)


if __name__ == "__main__":
    main()
