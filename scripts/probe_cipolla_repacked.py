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
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "cipolla_repacked_probe"
PLOTS_DIR = OUTPUT_DIR / "plots"

DATASET_ORDER = [
    "published_exact_grid_ge_1e4",
    "reproducible_exact_baseline",
    "reproducible_exact_stage_a",
    "reproducible_exact_stage_b",
]

DATASET_LABELS = {
    "published_exact_grid_ge_1e4": "published exact grid",
    "reproducible_exact_baseline": "baseline",
    "reproducible_exact_stage_a": "stage_a",
    "reproducible_exact_stage_b": "stage_b",
}

VARIANT_ORDER = [
    "c_n_fixed_k",
    "cipolla_log3_repacked",
    "cipolla_log4_repacked",
    "cipolla_log5_repacked",
    "cipolla_log6_repacked",
    "li_inverse_seed",
]

VARIANT_LABELS = {
    "c_n_fixed_k": "c_n + fixed k",
    "cipolla_log3_repacked": "log^3 repacked",
    "cipolla_log4_repacked": "log^4 repacked",
    "cipolla_log5_repacked": "log^5 repacked",
    "cipolla_log6_repacked": "log^6 repacked",
    "li_inverse_seed": "li_inverse_seed",
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
    6: [3478014, -2823180, 1075020, -246480, 35790, -3084, 120],
}


def load_known_primes_md(path: Path) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
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
            if n < 10_000:
                continue
            rows.append(
                {
                    "dataset": "published_exact_grid_ge_1e4",
                    "family": "published_exact_grid",
                    "n": n,
                    "p_n": p_n,
                }
            )
    return rows


def load_exact_csv(path: Path, dataset_name: str) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
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
            backbone_ratio = ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n)
            pnt = n_mp * backbone_ratio
            if pnt <= 0:
                pnt = n_mp
            ln_p = gp.log(pnt)
            basis[n_value] = {
                "P": float(pnt),
                "L": float(ln_n),
                "LL": float(ln_ln_n),
                "LP": float(ln_p),
                "B": float(backbone_ratio),
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


def repacked_kappa(basis_row: dict[str, float], upto_order: int) -> float:
    pnt = basis_row["P"]
    ln_n = basis_row["L"]
    ln_ln_n = basis_row["LL"]
    n_value = pnt / basis_row["B"]
    residual = 0.0
    for order in range(3, upto_order + 1):
        sign = 1.0 if order % 2 == 1 else -1.0
        residual += n_value * sign * cipolla_polynomial(order, ln_ln_n) / (ln_n**order)
    return residual / (pnt ** (2.0 / 3.0))


def estimate_variant(variant_name: str, n_value: int, basis_row: dict[str, float]) -> tuple[int, float]:
    if variant_name == "li_inverse_seed":
        return li_inverse_seed(n_value), math.nan

    pnt = basis_row["P"]
    ln_p = basis_row["LP"]
    c_value = c_n_value(basis_row)
    d_value = c_value * pnt * ((ln_p / (math.e**4)) ** 2)

    if variant_name == "c_n_fixed_k":
        kappa = 0.065
    elif variant_name == "cipolla_log3_repacked":
        kappa = repacked_kappa(basis_row, 3)
    elif variant_name == "cipolla_log4_repacked":
        kappa = repacked_kappa(basis_row, 4)
    elif variant_name == "cipolla_log5_repacked":
        kappa = repacked_kappa(basis_row, 5)
    elif variant_name == "cipolla_log6_repacked":
        kappa = repacked_kappa(basis_row, 6)
    else:
        raise ValueError(f"unknown variant: {variant_name}")

    estimate = math.floor(pnt + d_value + kappa * (pnt ** (2.0 / 3.0)) + 0.5)
    return estimate, kappa


def summarize(values: list[float]) -> dict[str, float]:
    arr = np.array(values, dtype=np.float64)
    return {
        "max_rel_ppm": float(arr.max()),
        "mean_rel_ppm": float(arr.mean()),
        "median_rel_ppm": float(np.median(arr)),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_dataset_summary(summary_rows: list[dict[str, object]]) -> None:
    non_li_variants = [name for name in VARIANT_ORDER if name != "li_inverse_seed"]
    x_positions = np.arange(len(non_li_variants))
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    axes = axes.flatten()

    for ax, dataset_name in zip(axes, DATASET_ORDER):
        max_values: list[float] = []
        li_value = math.nan
        for variant_name in VARIANT_ORDER:
            row = next(
                item
                for item in summary_rows
                if item["dataset"] == dataset_name and item["variant"] == variant_name
            )
            if variant_name == "li_inverse_seed":
                li_value = float(row["max_rel_ppm"])
            else:
                max_values.append(float(row["max_rel_ppm"]))

        ax.plot(x_positions, max_values, marker="o", color="#0b7285", linewidth=2)
        ax.axhline(li_value, color="#6741d9", linestyle="--", linewidth=1.5)
        ax.set_yscale("log")
        ax.set_xticks(x_positions)
        ax.set_xticklabels([VARIANT_LABELS[name] for name in non_li_variants], rotation=20, ha="right")
        ax.set_title(DATASET_LABELS[dataset_name])
        ax.set_ylabel("max seed ppm")
        ax.grid(True, axis="y", alpha=0.25)

    fig.suptitle("Exact dataset max seed ppm by derived order", fontsize=14)
    fig.savefig(PLOTS_DIR / "dataset_max_ppm_by_variant.png", dpi=180)
    plt.close(fig)


def plot_stage_family_order5_vs_li(family_rows: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    stages = ["reproducible_exact_stage_a", "reproducible_exact_stage_b"]
    colors = {
        "cipolla_log5_repacked": "#0b7285",
        "li_inverse_seed": "#6741d9",
    }

    for ax, dataset_name in zip(axes, stages):
        x = np.arange(len(FAMILY_ORDER))
        width = 0.36
        for offset, variant_name in [(-width / 2, "cipolla_log5_repacked"), (width / 2, "li_inverse_seed")]:
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
            ax.bar(x + offset, heights, width=width, label=VARIANT_LABELS[variant_name], color=colors[variant_name])
        ax.set_xticks(x)
        ax.set_xticklabels(FAMILY_ORDER, rotation=20, ha="right")
        ax.set_title(DATASET_LABELS[dataset_name])
        ax.set_ylabel("max seed ppm")
        ax.grid(True, axis="y", alpha=0.25)

    axes[0].legend()
    fig.suptitle("Large-regime family max seed ppm: order-5 repacked vs li_inverse_seed", fontsize=14)
    fig.savefig(PLOTS_DIR / "stage_family_max_ppm_order5_vs_li.png", dpi=180)
    plt.close(fig)


def plot_published_points(point_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
    for variant_name, color in [("cipolla_log5_repacked", "#0b7285"), ("li_inverse_seed", "#6741d9")]:
        subset = [row for row in point_rows if row["variant"] == variant_name]
        subset.sort(key=lambda row: int(row["n"]))
        ax.plot(
            [float(row["log10_n"]) for row in subset],
            [float(row["rel_ppm"]) for row in subset],
            marker="o",
            linewidth=2,
            color=color,
            label=VARIANT_LABELS[variant_name],
        )
    ax.set_yscale("log")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("seed ppm")
    ax.set_title("Published exact grid: order-5 repacked vs li_inverse_seed")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(PLOTS_DIR / "published_points_order5_vs_li.png", dpi=180)
    plt.close(fig)


def plot_order5_vs_grok_revised(point_rows: list[dict[str, object]]) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
    variant_styles = {
        "cipolla_log5_repacked": ("#0b7285", "cipolla_log5_repacked"),
        "grok_revised": ("#c92a2a", "grok_revised"),
    }
    for variant_name, (color, label) in variant_styles.items():
        subset = [row for row in point_rows if row["variant"] == variant_name]
        subset.sort(key=lambda row: int(row["n"]))
        ax.plot(
            [float(row["log10_n"]) for row in subset],
            [float(row["rel_ppm"]) for row in subset],
            marker="o",
            linewidth=2,
            color=color,
            label=label,
        )
    ax.set_yscale("log")
    ax.set_xlabel("log10(n)")
    ax.set_ylabel("seed ppm")
    ax.set_title("Published exact grid: order-5 repacked vs Grok revised")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.savefig(PLOTS_DIR / "published_points_order5_vs_grok_revised.png", dpi=180)
    plt.close(fig)


def write_readme(
    summary_rows: list[dict[str, object]],
    family_rows: list[dict[str, object]],
    published_point_rows: list[dict[str, object]],
) -> None:
    def find_summary(dataset_name: str, variant_name: str) -> dict[str, object]:
        return next(
            item
            for item in summary_rows
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

    order5_stage_a = find_summary("reproducible_exact_stage_a", "cipolla_log5_repacked")
    order5_stage_b = find_summary("reproducible_exact_stage_b", "cipolla_log5_repacked")
    li_stage_a = find_summary("reproducible_exact_stage_a", "li_inverse_seed")
    li_stage_b = find_summary("reproducible_exact_stage_b", "li_inverse_seed")
    order5_published = find_summary("published_exact_grid_ge_1e4", "cipolla_log5_repacked")
    li_published = find_summary("published_exact_grid_ge_1e4", "li_inverse_seed")
    order5_baseline = find_summary("reproducible_exact_baseline", "cipolla_log5_repacked")
    li_baseline = find_summary("reproducible_exact_baseline", "li_inverse_seed")

    def power_label(n_value: int) -> str:
        exponent = int(round(math.log10(n_value)))
        return f"10^{exponent}"

    published_points_by_n: dict[int, dict[str, float]] = {}
    for row in published_point_rows:
        n_value = int(row["n"])
        published_points_by_n.setdefault(n_value, {})
        published_points_by_n[n_value][str(row["variant"])] = float(row["rel_ppm"])

    winning_n_values = [
        n_value
        for n_value, values in sorted(published_points_by_n.items())
        if values["cipolla_log5_repacked"] < values["li_inverse_seed"]
    ]
    losing_n_values = [
        n_value
        for n_value, values in sorted(published_points_by_n.items())
        if values["cipolla_log5_repacked"] >= values["li_inverse_seed"]
    ]

    lines = [
        "# Consistent n-scale Cipolla Repacked Probe",
        "",
        "This probe tests one narrow question: whether a fully derived `k*(n)` can beat `li_inverse_seed` in the exact large regimes without introducing chosen coefficients.",
        "",
        "The construction keeps the existing backbone form, but derives both the bend and the lift from the same `n`-scale Cipolla expansion.",
        "",
        "Let",
        "",
        "$$ L = \\ln n $$",
        "",
        "$$ \\ell = \\ln\\ln n $$",
        "",
        "$$ P(n) = n\\left(L + \\ell - 1 + \\frac{\\ell - 2}{L}\\right) $$",
        "",
        "The bend term is the exact `1/log^2 n` Cipolla correction routed through the existing bend slot:",
        "",
        "$$ d(n) = -n\\frac{\\ell^2 - 6\\ell + 11}{2L^2} $$",
        "",
        "The order-5 candidate puts the next three Cipolla terms into the lift slot:",
        "",
        "$$ P_3(\\ell) = \\frac{2\\ell^3 - 21\\ell^2 + 84\\ell - 131}{6} $$",
        "",
        "$$ P_4(\\ell) = \\frac{6\\ell^4 - 92\\ell^3 + 588\\ell^2 - 1908\\ell + 2666}{24} $$",
        "",
        "$$ P_5(\\ell) = \\frac{24\\ell^5 - 490\\ell^4 + 4380\\ell^3 - 22020\\ell^2 + 62860\\ell - 81534}{120} $$",
        "",
        "$$ k_5^*(n) = \\frac{n(P_3(\\ell)/L^3 - P_4(\\ell)/L^4 + P_5(\\ell)/L^5)}{P(n)^{2/3}} $$",
        "",
        "$$ \\widehat{p}_n = round(P(n) + d(n) + k_5^*(n)P(n)^{2/3}) $$",
        "",
        "This is algebraically the Cipolla asymptotic expansion through `1/log^5 n`, repacked into the existing backbone + bend + lift structure.",
        "",
        "## Strongest Finding",
        "",
        "The order-5 repacked seed is the first fully derived candidate in this line that beats `li_inverse_seed` on the exact large-regime stage families already committed in the repository.",
        "",
        f"- `stage_a` max seed ppm: `cipolla_log5_repacked = {float(order5_stage_a['max_rel_ppm']):.6f}`, `li_inverse_seed = {float(li_stage_a['max_rel_ppm']):.6f}`",
        f"- `stage_b` max seed ppm: `cipolla_log5_repacked = {float(order5_stage_b['max_rel_ppm']):.6f}`, `li_inverse_seed = {float(li_stage_b['max_rel_ppm']):.6f}`",
        f"- published exact grid max seed ppm: `cipolla_log5_repacked = {float(order5_published['max_rel_ppm']):.6f}`, `li_inverse_seed = {float(li_published['max_rel_ppm']):.6f}`",
        f"- reproducible exact baseline max seed ppm: `cipolla_log5_repacked = {float(order5_baseline['max_rel_ppm']):.6f}`, `li_inverse_seed = {float(li_baseline['max_rel_ppm']):.6f}`",
        "",
        "Pointwise on the published power-of-ten grid, the order-5 repacked seed wins from "
        + f"`{power_label(winning_n_values[0])}` through `{power_label(winning_n_values[-1])}`"
        + " and then loses from "
        + f"`{power_label(losing_n_values[0])}` upward.",
        "",
        "## Large-Regime Family Split",
        "",
    ]

    for dataset_name in ["reproducible_exact_stage_a", "reproducible_exact_stage_b"]:
        lines.append(f"### {DATASET_LABELS[dataset_name]}")
        lines.append("")
        lines.append("| family | order-5 max ppm | li max ppm | order-5 mean ppm | li mean ppm | order-5 median ppm | li median ppm |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for family_name in FAMILY_ORDER:
            order5_row = find_family(dataset_name, family_name, "cipolla_log5_repacked")
            li_row = find_family(dataset_name, family_name, "li_inverse_seed")
            lines.append(
                "| "
                + family_name
                + f" | {float(order5_row['max_rel_ppm']):.6f}"
                + f" | {float(li_row['max_rel_ppm']):.6f}"
                + f" | {float(order5_row['mean_rel_ppm']):.6f}"
                + f" | {float(li_row['mean_rel_ppm']):.6f}"
                + f" | {float(order5_row['median_rel_ppm']):.6f}"
                + f" | {float(li_row['median_rel_ppm']):.6f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Artifacts",
            "",
            "- [dataset_summary.csv](./dataset_summary.csv)",
            "- [stage_family_summary.csv](./stage_family_summary.csv)",
            "- [published_point_comparison.csv](./published_point_comparison.csv)",
            "- [dataset_max_ppm_by_variant.png](./plots/dataset_max_ppm_by_variant.png)",
            "- [stage_family_max_ppm_order5_vs_li.png](./plots/stage_family_max_ppm_order5_vs_li.png)",
            "- [published_points_order5_vs_li.png](./plots/published_points_order5_vs_li.png)",
            "- [published_points_order5_vs_grok_revised.png](./plots/published_points_order5_vs_grok_revised.png)",
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

    unique_n_values = sorted({int(row["n"]) for row in rows})
    basis = compute_basis(unique_n_values)

    row_records: list[dict[str, object]] = []
    for row in rows:
        n_value = int(row["n"])
        p_n = int(row["p_n"])
        basis_row = basis[n_value]
        for variant_name in VARIANT_ORDER:
            estimate, kappa = estimate_variant(variant_name, n_value, basis_row)
            rel_ppm = abs(estimate - p_n) / p_n * 1e6
            row_records.append(
                {
                    "dataset": row["dataset"],
                    "family": row["family"],
                    "variant": variant_name,
                    "n": n_value,
                    "log10_n": math.log10(n_value),
                    "kappa": kappa,
                    "rel_ppm": rel_ppm,
                }
            )

    dataset_summary_rows: list[dict[str, object]] = []
    for dataset_name in DATASET_ORDER:
        for variant_name in VARIANT_ORDER:
            values = [
                float(row["rel_ppm"])
                for row in row_records
                if row["dataset"] == dataset_name and row["variant"] == variant_name
            ]
            summary = summarize(values)
            dataset_summary_rows.append(
                {
                    "dataset": dataset_name,
                    "variant": variant_name,
                    **summary,
                }
            )

    family_summary_rows: list[dict[str, object]] = []
    for dataset_name in ["reproducible_exact_stage_a", "reproducible_exact_stage_b"]:
        for family_name in FAMILY_ORDER:
            for variant_name in VARIANT_ORDER:
                values = [
                    float(row["rel_ppm"])
                    for row in row_records
                    if row["dataset"] == dataset_name
                    and row["family"] == family_name
                    and row["variant"] == variant_name
                ]
                summary = summarize(values)
                family_summary_rows.append(
                    {
                        "dataset": dataset_name,
                        "family": family_name,
                        "variant": variant_name,
                        **summary,
                    }
                )

    published_point_rows = [
        {
            "variant": row["variant"],
            "n": row["n"],
            "log10_n": row["log10_n"],
            "rel_ppm": row["rel_ppm"],
        }
        for row in row_records
        if row["dataset"] == "published_exact_grid_ge_1e4"
        and row["variant"] in {"cipolla_log5_repacked", "li_inverse_seed"}
    ]

    grok_published_rows: list[dict[str, object]] = []
    for row in rows:
        if row["dataset"] != "published_exact_grid_ge_1e4":
            continue
        n_value = int(row["n"])
        p_n = int(row["p_n"])
        basis_row = basis[n_value]
        estimate, _ = estimate_variant("cipolla_log5_repacked", n_value, basis_row)
        rel_ppm = abs(estimate - p_n) / p_n * 1e6
        grok_published_rows.append(
            {
                "variant": "cipolla_log5_repacked",
                "n": n_value,
                "log10_n": math.log10(n_value),
                "rel_ppm": rel_ppm,
            }
        )

        pnt = basis_row["P"]
        ln_n = basis_row["L"]
        ln_ln_n = basis_row["LL"]
        ln_p = basis_row["LP"]
        # Grok revised is the first-order truncated lift paired with the earlier P-scale asymptotic bend.
        c_value = -((math.e**8) * ((math.log(ln_p) ** 2) - 6.0 * math.log(ln_p) + 11.0)) / (2.0 * (ln_p**5))
        kappa = (2.0 * basis_row["B"] + math.e**2) / (4.0 * (math.e**2) * basis_row["B"])
        estimate = math.floor(pnt + c_value * pnt * ((ln_p / (math.e**4)) ** 2) + kappa * (pnt ** (2.0 / 3.0)) + 0.5)
        rel_ppm = abs(estimate - p_n) / p_n * 1e6
        grok_published_rows.append(
            {
                "variant": "grok_revised",
                "n": n_value,
                "log10_n": math.log10(n_value),
                "rel_ppm": rel_ppm,
            }
        )

    write_csv(
        OUTPUT_DIR / "dataset_summary.csv",
        ["dataset", "variant", "max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"],
        dataset_summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "stage_family_summary.csv",
        ["dataset", "family", "variant", "max_rel_ppm", "mean_rel_ppm", "median_rel_ppm"],
        family_summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "published_point_comparison.csv",
        ["variant", "n", "log10_n", "rel_ppm"],
        published_point_rows,
    )

    plot_dataset_summary(dataset_summary_rows)
    plot_stage_family_order5_vs_li(family_summary_rows)
    plot_published_points(published_point_rows)
    plot_order5_vs_grok_revised(grok_published_rows)
    write_readme(dataset_summary_rows, family_summary_rows, published_point_rows)


if __name__ == "__main__":
    main()
