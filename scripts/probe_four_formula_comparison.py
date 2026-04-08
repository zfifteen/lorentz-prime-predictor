#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import gmpy2 as gp
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np
from sympy import mobius


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "four_formula_comparison"
PLOTS_DIR = OUTPUT_DIR / "plots"
PYTHON_SRC = REPO_ROOT / "src" / "python"

if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from lpp.predictor import lpp_seed  # noqa: E402


DATASET_ORDER = [
    "published_exact_grid_ge_1e4",
    "reproducible_exact_baseline",
    "reproducible_exact_stage_a",
    "reproducible_exact_stage_b",
    "local_continuation_stage_c",
]

DATASET_LABELS = {
    "published_exact_grid_ge_1e4": "published exact grid",
    "reproducible_exact_baseline": "baseline",
    "reproducible_exact_stage_a": "stage_a",
    "reproducible_exact_stage_b": "stage_b",
    "local_continuation_stage_c": "stage_c local",
}

VARIANT_ORDER = [
    "lpp_seed",
    "cipolla_log5_repacked",
    "r_inverse_seed",
    "li_inverse_seed",
]

VARIANT_LABELS = {
    "lpp_seed": "lpp_seed",
    "cipolla_log5_repacked": "cipolla_log5_repacked",
    "r_inverse_seed": "r_inverse_seed",
    "li_inverse_seed": "li_inverse_seed",
}

VARIANT_COLORS = {
    "lpp_seed": "#1f77b4",
    "cipolla_log5_repacked": "#0b7285",
    "r_inverse_seed": "#c92a2a",
    "li_inverse_seed": "#6741d9",
}

FAMILY_ORDER = [
    "boundary_window",
    "dense_local_window",
    "off_lattice_decimal",
]

CIPOLLA_RAW_POLYNOMIALS = {
    3: [-131, 84, -21, 2],
    4: [2666, -1908, 588, -92, 6],
    5: [-81534, 62860, -22020, 4380, -490, 24],
}

ANCHOR_N_VALUES = [
    10**12,
    10**14,
    10**15,
    10**16,
    10**17,
    10**18,
]


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
                n_value = int(parts[0].replace(",", "").replace("_", ""))
                p_n = int(parts[2].replace(",", "").replace("_", ""))
            except ValueError:
                continue
            if n_value < 10_000:
                continue
            rows.append(
                {
                    "dataset": "published_exact_grid_ge_1e4",
                    "family": "published_exact_grid",
                    "n": n_value,
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


def compute_basis(unique_n_values: list[int]) -> dict[int, dict[str, float]]:
    basis: dict[int, dict[str, float]] = {}
    for n_value in unique_n_values:
        precision = max(256, int(gp.log2(n_value)) + 256)
        with gp.context(gp.get_context(), precision=precision):
            n_mp = gp.mpfr(n_value)
            ln_n = gp.log(n_mp)
            ln_ln_n = gp.log(ln_n)
            pnt = n_mp * (ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n))
            if pnt <= 0:
                pnt = n_mp
            ln_p = gp.log(pnt)
            basis[n_value] = {
                "P": float(pnt),
                "L": float(ln_n),
                "LL": float(ln_ln_n),
                "LP": float(ln_p),
                "B": float(pnt / n_mp),
            }
    return basis


def c_n_value(basis_row: dict[str, float]) -> float:
    ln_n = basis_row["L"]
    ln_ln_n = basis_row["LL"]
    ln_p = basis_row["LP"]
    backbone_ratio = basis_row["B"]
    poly2 = (ln_ln_n**2) - 6.0 * ln_ln_n + 11.0
    return -poly2 / (2.0 * (ln_n**2) * backbone_ratio * ((ln_p / (math.e**4)) ** 2))


def cipolla_polynomial(order: int, ln_ln_n: float) -> float:
    coefficients = CIPOLLA_RAW_POLYNOMIALS[order]
    total = 0.0
    for power, coefficient in enumerate(coefficients):
        total += coefficient * (ln_ln_n**power)
    return total / math.factorial(order)


def repacked_kappa_order5(basis_row: dict[str, float]) -> float:
    pnt = basis_row["P"]
    ln_n = basis_row["L"]
    ln_ln_n = basis_row["LL"]
    n_value = pnt / basis_row["B"]
    residual = 0.0
    for order in range(3, 6):
        sign = 1.0 if order % 2 == 1 else -1.0
        residual += n_value * sign * cipolla_polynomial(order, ln_ln_n) / (ln_n**order)
    return residual / (pnt ** (2.0 / 3.0))


def cipolla_log5_repacked_seed(n_value: int, basis_row: dict[str, float]) -> int:
    pnt = basis_row["P"]
    ln_p = basis_row["LP"]
    c_value = c_n_value(basis_row)
    d_value = c_value * pnt * ((ln_p / (math.e**4)) ** 2)
    kappa = repacked_kappa_order5(basis_row)
    estimate = pnt + d_value + kappa * (pnt ** (2.0 / 3.0))
    return math.floor(estimate + 0.5)


def riemann_r(x_value: mp.mpf, truncation_k: int) -> mp.mpf:
    total = mp.mpf("0")
    for k_value in range(1, truncation_k + 1):
        mu_value = mobius(k_value)
        if mu_value == 0:
            continue
        total += mp.mpf(mu_value) / k_value * mp.li(x_value ** (mp.mpf(1) / k_value))
    return total


def riemann_r_derivative(x_value: mp.mpf, truncation_k: int) -> mp.mpf:
    total = mp.mpf("0")
    for k_value in range(1, truncation_k + 1):
        mu_value = mobius(k_value)
        if mu_value == 0:
            continue
        total += mp.mpf(mu_value) / k_value * (x_value ** (mp.mpf(1) / k_value - 1))
    return total / mp.log(x_value)


def r_inverse_seed(n_value: int, basis_row: dict[str, float], truncation_k: int = 8, newton_steps: int = 2) -> int:
    mp.mp.dps = 100
    x_value = mp.mpf(cipolla_log5_repacked_seed(n_value, basis_row))
    target = mp.mpf(n_value)
    for _ in range(newton_steps):
        x_value -= (riemann_r(x_value, truncation_k) - target) / riemann_r_derivative(x_value, truncation_k)
    return int(gp.mpz(x_value + 0.5))


def estimate_variant(variant_name: str, n_value: int, basis_row: dict[str, float]) -> int:
    if variant_name == "lpp_seed":
        return lpp_seed(n_value)
    if variant_name == "cipolla_log5_repacked":
        return cipolla_log5_repacked_seed(n_value, basis_row)
    if variant_name == "r_inverse_seed":
        return r_inverse_seed(n_value, basis_row)
    if variant_name == "li_inverse_seed":
        return li_inverse_seed(n_value)
    raise ValueError(f"unknown variant: {variant_name}")


def summarize(values: list[float]) -> dict[str, float]:
    array = np.array(values, dtype=np.float64)
    return {
        "max_rel_ppm": float(array.max()),
        "mean_rel_ppm": float(array.mean()),
        "median_rel_ppm": float(np.median(array)),
        "rms_rel_ppm": float(np.sqrt(np.mean(np.square(array)))),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_dataset_metric(summary_rows: list[dict[str, object]], metric_key: str, filename: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.0), constrained_layout=True)
    x_positions = np.arange(len(DATASET_ORDER))
    width = 0.18
    offsets = {
        "lpp_seed": -1.5 * width,
        "cipolla_log5_repacked": -0.5 * width,
        "r_inverse_seed": 0.5 * width,
        "li_inverse_seed": 1.5 * width,
    }

    for variant_name in VARIANT_ORDER:
        heights = []
        for dataset_name in DATASET_ORDER:
            row = next(
                item
                for item in summary_rows
                if item["dataset"] == dataset_name and item["variant"] == variant_name
            )
            heights.append(float(row[metric_key]))
        ax.bar(
            x_positions + offsets[variant_name],
            heights,
            width=width,
            color=VARIANT_COLORS[variant_name],
            label=VARIANT_LABELS[variant_name],
        )

    ax.set_yscale("log")
    ax.set_xticks(x_positions)
    ax.set_xticklabels([DATASET_LABELS[name] for name in DATASET_ORDER], rotation=15, ha="right")
    ax.set_ylabel(metric_key.replace("_", " "))
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(PLOTS_DIR / filename, dpi=180)
    plt.close(fig)


def plot_exact_stage_family_max(family_rows: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)
    stage_names = ["reproducible_exact_stage_a", "reproducible_exact_stage_b"]
    width = 0.18
    offsets = {
        "lpp_seed": -1.5 * width,
        "cipolla_log5_repacked": -0.5 * width,
        "r_inverse_seed": 0.5 * width,
        "li_inverse_seed": 1.5 * width,
    }

    for ax, dataset_name in zip(axes, stage_names):
        x_positions = np.arange(len(FAMILY_ORDER))
        for variant_name in VARIANT_ORDER:
            heights = []
            for family_name in FAMILY_ORDER:
                row = next(
                    item
                    for item in family_rows
                    if item["dataset"] == dataset_name
                    and item["family"] == family_name
                    and item["variant"] == variant_name
                )
                heights.append(float(row["max_rel_ppm"]))
            ax.bar(
                x_positions + offsets[variant_name],
                heights,
                width=width,
                color=VARIANT_COLORS[variant_name],
                label=VARIANT_LABELS[variant_name],
            )
        ax.set_yscale("log")
        ax.set_xticks(x_positions)
        ax.set_xticklabels(FAMILY_ORDER, rotation=20, ha="right")
        ax.set_title(DATASET_LABELS[dataset_name])
        ax.set_ylabel("max seed ppm")
        ax.grid(True, axis="y", alpha=0.25)

    axes[0].legend()
    fig.suptitle("Exact stage family max seed ppm", fontsize=14)
    fig.savefig(PLOTS_DIR / "exact_stage_family_max_ppm.png", dpi=180)
    plt.close(fig)


def plot_local_continuation_family_max(family_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 4.8), constrained_layout=True)
    x_positions = np.arange(len(FAMILY_ORDER))
    width = 0.18
    offsets = {
        "lpp_seed": -1.5 * width,
        "cipolla_log5_repacked": -0.5 * width,
        "r_inverse_seed": 0.5 * width,
        "li_inverse_seed": 1.5 * width,
    }

    for variant_name in VARIANT_ORDER:
        heights = []
        for family_name in FAMILY_ORDER:
            row = next(
                item
                for item in family_rows
                if item["dataset"] == "local_continuation_stage_c"
                and item["family"] == family_name
                and item["variant"] == variant_name
            )
            heights.append(float(row["max_rel_ppm"]))
        ax.bar(
            x_positions + offsets[variant_name],
            heights,
            width=width,
            color=VARIANT_COLORS[variant_name],
            label=VARIANT_LABELS[variant_name],
        )

    ax.set_yscale("log")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(FAMILY_ORDER, rotation=20, ha="right")
    ax.set_ylabel("max seed ppm")
    ax.set_title("Local continuation family max seed ppm")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(PLOTS_DIR / "local_continuation_family_max_ppm.png", dpi=180)
    plt.close(fig)


def plot_exact_anchor_comparison(anchor_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 4.8), constrained_layout=True)
    for variant_name in VARIANT_ORDER:
        subset = [row for row in anchor_rows if row["variant"] == variant_name]
        subset.sort(key=lambda row: int(row["n"]))
        ax.plot(
            [float(row["log10_n"]) for row in subset],
            [float(row["rel_ppm"]) for row in subset],
            marker="o",
            linewidth=2,
            color=VARIANT_COLORS[variant_name],
            label=VARIANT_LABELS[variant_name],
        )

    ax.set_yscale("log")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("seed ppm")
    ax.set_title("Exact anchors through 10^18")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(PLOTS_DIR / "exact_anchor_comparison.png", dpi=180)
    plt.close(fig)


def write_readme(
    dataset_summary_rows: list[dict[str, object]],
    family_rows: list[dict[str, object]],
    anchor_rows: list[dict[str, object]],
) -> None:
    def find_summary(dataset_name: str, variant_name: str) -> dict[str, object]:
        return next(
            item
            for item in dataset_summary_rows
            if item["dataset"] == dataset_name and item["variant"] == variant_name
        )

    def find_family(dataset_name: str, family_name: str, variant_name: str) -> dict[str, object]:
        return next(
            item
            for item in family_rows
            if item["dataset"] == dataset_name
            and item["family"] == family_name
            and item["variant"] == variant_name
        )

    lines = [
        "# Four-Formula Comparison",
        "",
        "This benchmark suite compares four formulas on the repository's declared comparison horizon:",
        "",
        "- `lpp_seed`",
        "- `cipolla_log5_repacked`",
        "- `r_inverse_seed`",
        "- `li_inverse_seed`",
        "",
        "The exact datasets are the published exact grid, the reproducible exact baseline, exact `stage_a`, and exact `stage_b`.",
        "The local continuation dataset is reported separately as `stage_c local`.",
        "",
        "## Strongest Findings",
        "",
    ]

    stage_b_r = find_summary("reproducible_exact_stage_b", "r_inverse_seed")
    stage_b_li = find_summary("reproducible_exact_stage_b", "li_inverse_seed")
    stage_c_dense_lpp = find_family("local_continuation_stage_c", "dense_local_window", "lpp_seed")
    stage_c_dense_li = find_family("local_continuation_stage_c", "dense_local_window", "li_inverse_seed")
    stage_c_decimal_lpp = find_family("local_continuation_stage_c", "off_lattice_decimal", "lpp_seed")
    stage_c_decimal_li = find_family("local_continuation_stage_c", "off_lattice_decimal", "li_inverse_seed")

    lines.extend(
        [
            "On the exact deep held-out stages, `r_inverse_seed` is the strongest candidate in this four-formula set.",
            f"- exact `stage_b` max ppm: `r_inverse_seed = {float(stage_b_r['max_rel_ppm']):.6f}`, `li_inverse_seed = {float(stage_b_li['max_rel_ppm']):.6f}`",
            "",
            "On the local continuation off-anchor families, the picture flips because the labels come from the Z5D continuation family rather than exact primes.",
            f"- local `dense_local_window` max ppm: `lpp_seed = {float(stage_c_dense_lpp['max_rel_ppm']):.12f}`, `li_inverse_seed = {float(stage_c_dense_li['max_rel_ppm']):.6f}`",
            f"- local `off_lattice_decimal` max ppm: `lpp_seed = {float(stage_c_decimal_lpp['max_rel_ppm']):.12f}`, `li_inverse_seed = {float(stage_c_decimal_li['max_rel_ppm']):.6f}`",
            "",
            "## Exact Anchor Snapshot",
            "",
        ]
    )

    for n_value in ANCHOR_N_VALUES:
        subset = [row for row in anchor_rows if int(row["n"]) == n_value]
        subset.sort(key=lambda row: VARIANT_ORDER.index(str(row["variant"])))
        parts = [f"`{row['variant']} = {float(row['rel_ppm']):.6f}` ppm" for row in subset]
        lines.append(f"- `10^{int(round(math.log10(n_value)))}`: " + ", ".join(parts))
    lines.append("")

    lines.extend(
        [
            "## Exact Family Snapshot",
            "",
            "### stage_a",
            "",
        ]
    )
    for family_name in FAMILY_ORDER:
        parts = []
        for variant_name in VARIANT_ORDER:
            row = find_family("reproducible_exact_stage_a", family_name, variant_name)
            parts.append(f"`{variant_name} = {float(row['max_rel_ppm']):.6f}`")
        lines.append(f"- `{family_name}` max ppm: " + ", ".join(parts))
    lines.extend(["", "### stage_b", ""])
    for family_name in FAMILY_ORDER:
        parts = []
        for variant_name in VARIANT_ORDER:
            row = find_family("reproducible_exact_stage_b", family_name, variant_name)
            parts.append(f"`{variant_name} = {float(row['max_rel_ppm']):.6f}`")
        lines.append(f"- `{family_name}` max ppm: " + ", ".join(parts))

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- [dataset_summary.csv](./dataset_summary.csv)",
            "- [stage_family_summary.csv](./stage_family_summary.csv)",
            "- [anchor_comparison.csv](./anchor_comparison.csv)",
            "- [rowwise_results.csv](./rowwise_results.csv)",
            "- [dataset_mean_ppm.png](./plots/dataset_mean_ppm.png)",
            "- [dataset_max_ppm.png](./plots/dataset_max_ppm.png)",
            "- [exact_stage_family_max_ppm.png](./plots/exact_stage_family_max_ppm.png)",
            "- [local_continuation_family_max_ppm.png](./plots/local_continuation_family_max_ppm.png)",
            "- [exact_anchor_comparison.png](./plots/exact_anchor_comparison.png)",
            "",
        ]
    )

    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_known_primes_md(DATA_DIR / "KNOWN_PRIMES.md")
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e4_1e12.csv", "reproducible_exact_baseline"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e13_1e14.csv", "reproducible_exact_stage_a"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_exact_primes_1e15_1e16.csv", "reproducible_exact_stage_b"))
    rows.extend(load_exact_csv(DATA_DIR / "held_out_z5d_primes_1e17_1e18.csv", "local_continuation_stage_c"))

    unique_n_values = sorted({int(row["n"]) for row in rows})
    basis = compute_basis(unique_n_values)

    estimates_by_variant: dict[str, dict[int, int]] = {name: {} for name in VARIANT_ORDER}
    for n_value in unique_n_values:
        basis_row = basis[n_value]
        for variant_name in VARIANT_ORDER:
            estimates_by_variant[variant_name][n_value] = estimate_variant(variant_name, n_value, basis_row)

    rowwise_results: list[dict[str, object]] = []
    for row in rows:
        dataset_name = str(row["dataset"])
        family_name = str(row["family"])
        n_value = int(row["n"])
        p_n = int(row["p_n"])
        for variant_name in VARIANT_ORDER:
            estimate = estimates_by_variant[variant_name][n_value]
            rel_ppm = abs(estimate - p_n) / p_n * 1e6
            rowwise_results.append(
                {
                    "dataset": dataset_name,
                    "family": family_name,
                    "variant": variant_name,
                    "n": n_value,
                    "log10_n": math.log10(n_value),
                    "estimate": estimate,
                    "p_n": p_n,
                    "rel_ppm": rel_ppm,
                }
            )

    dataset_summary_rows: list[dict[str, object]] = []
    for dataset_name in DATASET_ORDER:
        for variant_name in VARIANT_ORDER:
            values = [
                float(row["rel_ppm"])
                for row in rowwise_results
                if row["dataset"] == dataset_name and row["variant"] == variant_name
            ]
            dataset_summary_rows.append(
                {
                    "dataset": dataset_name,
                    "variant": variant_name,
                    **summarize(values),
                }
            )

    family_summary_rows: list[dict[str, object]] = []
    for dataset_name in ["reproducible_exact_stage_a", "reproducible_exact_stage_b", "local_continuation_stage_c"]:
        for family_name in FAMILY_ORDER:
            for variant_name in VARIANT_ORDER:
                values = [
                    float(row["rel_ppm"])
                    for row in rowwise_results
                    if row["dataset"] == dataset_name
                    and row["family"] == family_name
                    and row["variant"] == variant_name
                ]
                family_summary_rows.append(
                    {
                        "dataset": dataset_name,
                        "family": family_name,
                        "variant": variant_name,
                        **summarize(values),
                    }
                )

    anchor_rows = [
        row
        for row in rowwise_results
        if row["dataset"] == "published_exact_grid_ge_1e4" and int(row["n"]) in ANCHOR_N_VALUES
    ]
    anchor_rows.sort(key=lambda row: (int(row["n"]), VARIANT_ORDER.index(str(row["variant"]))))
    anchor_csv_rows = [
        {
            "n": row["n"],
            "log10_n": row["log10_n"],
            "variant": row["variant"],
            "estimate": row["estimate"],
            "p_n": row["p_n"],
            "rel_ppm": row["rel_ppm"],
        }
        for row in anchor_rows
    ]

    write_csv(
        OUTPUT_DIR / "rowwise_results.csv",
        ["dataset", "family", "variant", "n", "log10_n", "estimate", "p_n", "rel_ppm"],
        rowwise_results,
    )
    write_csv(
        OUTPUT_DIR / "dataset_summary.csv",
        ["dataset", "variant", "max_rel_ppm", "mean_rel_ppm", "median_rel_ppm", "rms_rel_ppm"],
        dataset_summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "stage_family_summary.csv",
        ["dataset", "family", "variant", "max_rel_ppm", "mean_rel_ppm", "median_rel_ppm", "rms_rel_ppm"],
        family_summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "anchor_comparison.csv",
        ["n", "log10_n", "variant", "estimate", "p_n", "rel_ppm"],
        anchor_csv_rows,
    )

    plot_dataset_metric(
        dataset_summary_rows,
        "mean_rel_ppm",
        "dataset_mean_ppm.png",
        "Dataset mean seed ppm by formula",
    )
    plot_dataset_metric(
        dataset_summary_rows,
        "max_rel_ppm",
        "dataset_max_ppm.png",
        "Dataset max seed ppm by formula",
    )
    plot_exact_stage_family_max(family_summary_rows)
    plot_local_continuation_family_max(family_summary_rows)
    plot_exact_anchor_comparison(anchor_rows)
    write_readme(dataset_summary_rows, family_summary_rows, anchor_rows)


if __name__ == "__main__":
    main()
