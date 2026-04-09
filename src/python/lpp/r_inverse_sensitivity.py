from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

from .predictor import (
    _basis_row,
    _repacked_kappa_order5,
    _require_index,
    _riemann_r,
    _riemann_r_derivative,
    _c_n_value,
    cipolla_log5_repacked_seed,
    li_inverse_seed,
    r_inverse_seed,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
ANCHOR_DATASET = "official_exact_anchors"
SCENARIO_ORDER = [
    "baseline",
    "c_minus_10",
    "c_plus_10",
    "kappa_minus_10",
    "kappa_plus_10",
]
SCENARIO_SPECS = {
    "baseline": {
        "label": "baseline shipped",
        "c_scale": 1.0,
        "kappa_scale": 1.0,
    },
    "c_minus_10": {
        "label": "c term -10%",
        "c_scale": 0.9,
        "kappa_scale": 1.0,
    },
    "c_plus_10": {
        "label": "c term +10%",
        "c_scale": 1.1,
        "kappa_scale": 1.0,
    },
    "kappa_minus_10": {
        "label": "kappa term -10%",
        "c_scale": 1.0,
        "kappa_scale": 0.9,
    },
    "kappa_plus_10": {
        "label": "kappa term +10%",
        "c_scale": 1.0,
        "kappa_scale": 1.1,
    },
}
EXACT_DATASET_SPECS = [
    {
        "dataset": "reproducible_exact_stage_a",
        "source_label": "reproducible exact",
        "exact_labels": True,
        "path": DATA_DIR / "held_out_exact_primes_1e13_1e14.csv",
    },
    {
        "dataset": "reproducible_exact_stage_b",
        "source_label": "reproducible exact",
        "exact_labels": True,
        "path": DATA_DIR / "held_out_exact_primes_1e15_1e16.csv",
    },
]
LOCAL_DATASET_SPEC = {
    "dataset": "local_continuation_stage_c",
    "source_label": "local continuation",
    "exact_labels": False,
    "path": DATA_DIR / "held_out_z5d_primes_1e17_1e18.csv",
}
FAMILY_ORDER = ["published_exact_grid", "boundary_window", "dense_local_window", "off_lattice_decimal"]


def launch_components(
    n: int,
    *,
    c_scale: float = 1.0,
    kappa_scale: float = 1.0,
) -> dict[str, float]:
    n = _require_index(n)
    basis_row = _basis_row(n)
    pnt = basis_row["P"]
    ln_p = basis_row["LP"]
    c_value = _c_n_value(basis_row)
    base_d_term = c_value * pnt * ((ln_p / (math.e**4)) ** 2)
    base_kappa_value = _repacked_kappa_order5(basis_row)
    base_kappa_term = base_kappa_value * (pnt ** (2.0 / 3.0))
    d_term = c_scale * base_d_term
    kappa_term = kappa_scale * base_kappa_term
    estimate = math.floor(pnt + d_term + kappa_term + 0.5)
    return {
        "pnt": pnt,
        "base_d_term": base_d_term,
        "base_kappa_term": base_kappa_term,
        "d_term": d_term,
        "kappa_term": kappa_term,
        "estimate": estimate,
    }


def cipolla_log5_repacked_seed_with_scales(
    n: int,
    *,
    c_scale: float = 1.0,
    kappa_scale: float = 1.0,
) -> int:
    n = _require_index(n)
    if n < 100:
        return cipolla_log5_repacked_seed(n)
    return int(launch_components(n, c_scale=c_scale, kappa_scale=kappa_scale)["estimate"])


def r_inverse_seed_with_scales(
    n: int,
    *,
    c_scale: float = 1.0,
    kappa_scale: float = 1.0,
    truncation_k: int = 8,
    newton_steps: int = 2,
) -> int:
    n = _require_index(n)
    if n < 100:
        return r_inverse_seed(n, truncation_k=truncation_k, newton_steps=newton_steps)

    import gmpy2 as gp
    import mpmath as mp

    mp.mp.dps = 100
    x_value = mp.mpf(cipolla_log5_repacked_seed_with_scales(n, c_scale=c_scale, kappa_scale=kappa_scale))
    target = mp.mpf(n)
    for _ in range(newton_steps):
        x_value -= (_riemann_r(x_value, truncation_k) - target) / _riemann_r_derivative(x_value, truncation_k)
    return int(gp.mpz(x_value + 0.5))


def _load_known_primes_md(path: Path) -> list[dict[str, int | str]]:
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
            if n_value < 100 or n_value > 10**18:
                continue
            rows.append(
                {
                    "dataset": ANCHOR_DATASET,
                    "source_label": "published exact",
                    "exact_labels": True,
                    "row_id": f"anchor__n{n_value}",
                    "family": "published_exact_grid",
                    "decade_exponent": int(math.log10(n_value)),
                    "n": n_value,
                    "p_n": p_n,
                }
            )
    return rows


def _load_csv_dataset(spec: dict[str, object]) -> list[dict[str, int | str | bool]]:
    path = Path(spec["path"])
    rows: list[dict[str, int | str | bool]] = []
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "dataset": str(spec["dataset"]),
                    "source_label": str(spec["source_label"]),
                    "exact_labels": bool(spec["exact_labels"]),
                    "row_id": row["row_id"],
                    "family": row["family"],
                    "decade_exponent": int(row["decade_exponent"]),
                    "n": int(row["n"]),
                    "p_n": int(row["p_n"]),
                }
            )
    return rows


def load_sensitivity_datasets() -> list[dict[str, int | str | bool]]:
    rows = _load_known_primes_md(DATA_DIR / "KNOWN_PRIMES.md")
    for spec in EXACT_DATASET_SPECS:
        rows.extend(_load_csv_dataset(spec))
    rows.extend(_load_csv_dataset(LOCAL_DATASET_SPEC))
    return rows


def build_sensitivity_result_rows(
    dataset_rows: list[dict[str, int | str | bool]],
) -> list[dict[str, int | str | float | bool]]:
    li_cache: dict[int, int] = {}
    scenario_cache: dict[tuple[int, str], tuple[int, int]] = {}
    results: list[dict[str, int | str | float | bool]] = []
    for row in dataset_rows:
        n_value = int(row["n"])
        p_n = int(row["p_n"])
        if n_value not in li_cache:
            li_cache[n_value] = li_inverse_seed(n_value)
        li_seed = li_cache[n_value]
        li_signed_error = li_seed - p_n
        li_absolute_error = abs(li_signed_error)
        li_rel_ppm = (li_absolute_error / p_n) * 1e6
        for scenario in SCENARIO_ORDER:
            spec = SCENARIO_SPECS[scenario]
            c_scale = float(spec["c_scale"])
            kappa_scale = float(spec["kappa_scale"])
            cache_key = (n_value, scenario)
            if cache_key not in scenario_cache:
                scenario_cache[cache_key] = (
                    cipolla_log5_repacked_seed_with_scales(
                        n_value,
                        c_scale=c_scale,
                        kappa_scale=kappa_scale,
                    ),
                    r_inverse_seed_with_scales(
                        n_value,
                        c_scale=c_scale,
                        kappa_scale=kappa_scale,
                    ),
                )
            launch_seed, seed = scenario_cache[cache_key]
            seed_signed_error = seed - p_n
            seed_absolute_error = abs(seed_signed_error)
            seed_rel_ppm = (seed_absolute_error / p_n) * 1e6
            results.append(
                {
                    "dataset": row["dataset"],
                    "source_label": row["source_label"],
                    "exact_labels": row["exact_labels"],
                    "row_id": row["row_id"],
                    "family": row["family"],
                    "decade_exponent": row["decade_exponent"],
                    "n": n_value,
                    "p_n": p_n,
                    "scenario": scenario,
                    "scenario_label": spec["label"],
                    "c_scale": c_scale,
                    "kappa_scale": kappa_scale,
                    "launch_seed": launch_seed,
                    "seed": seed,
                    "seed_signed_error": seed_signed_error,
                    "seed_absolute_error": seed_absolute_error,
                    "seed_rel_ppm": seed_rel_ppm,
                    "li_inverse_seed": li_seed,
                    "li_inverse_signed_error": li_signed_error,
                    "li_inverse_absolute_error": li_absolute_error,
                    "li_inverse_rel_ppm": li_rel_ppm,
                    "advantage_vs_li_ppm": li_rel_ppm - seed_rel_ppm,
                }
            )
    return results


def summarize_family_results(
    rows: list[dict[str, int | str | float | bool]],
) -> list[dict[str, int | str | float | bool]]:
    grouped: dict[tuple[str, str, str], list[dict[str, int | str | float | bool]]] = {}
    for row in rows:
        key = (str(row["dataset"]), str(row["family"]), str(row["scenario"]))
        grouped.setdefault(key, []).append(row)

    summary_rows: list[dict[str, int | str | float | bool]] = []
    for dataset, family, scenario in sorted(grouped):
        group = grouped[(dataset, family, scenario)]
        seed_ppm_values = [float(row["seed_rel_ppm"]) for row in group]
        li_ppm_values = [float(row["li_inverse_rel_ppm"]) for row in group]
        example = group[0]
        summary_rows.append(
            {
                "dataset": dataset,
                "source_label": example["source_label"],
                "exact_labels": example["exact_labels"],
                "family": family,
                "scenario": scenario,
                "scenario_label": example["scenario_label"],
                "c_scale": example["c_scale"],
                "kappa_scale": example["kappa_scale"],
                "row_count": len(group),
                "max_rel_ppm": max(seed_ppm_values),
                "mean_rel_ppm": sum(seed_ppm_values) / len(seed_ppm_values),
                "median_rel_ppm": statistics.median(seed_ppm_values),
                "li_inverse_max_rel_ppm": max(li_ppm_values),
                "li_inverse_mean_rel_ppm": sum(li_ppm_values) / len(li_ppm_values),
                "li_inverse_median_rel_ppm": statistics.median(li_ppm_values),
                "wins_vs_li_on_max": max(seed_ppm_values) < max(li_ppm_values),
                "wins_vs_li_on_mean": (sum(seed_ppm_values) / len(seed_ppm_values)) < (sum(li_ppm_values) / len(li_ppm_values)),
            }
        )
    return summary_rows


def build_anchor_summary(
    rows: list[dict[str, int | str | float | bool]],
) -> list[dict[str, int | str | float | bool]]:
    anchor_rows = [row for row in rows if str(row["dataset"]) == ANCHOR_DATASET]
    anchor_rows.sort(key=lambda row: (int(row["n"]), SCENARIO_ORDER.index(str(row["scenario"]))))
    return anchor_rows


def _write_csv(
    path: Path,
    rows: list[dict[str, int | str | float | bool]],
    fieldnames: list[str],
) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fieldnames})


def _plot_family_summary(
    summary_rows: list[dict[str, int | str | float | bool]],
    *,
    datasets: list[str],
    output_path: Path,
    title: str,
) -> None:
    filtered = [row for row in summary_rows if str(row["dataset"]) in datasets]
    family_scenarios = [
        row
        for family in FAMILY_ORDER
        for scenario in SCENARIO_ORDER
        for row in filtered
        if str(row["family"]) == family and str(row["scenario"]) == scenario
    ]
    if not family_scenarios:
        return
    labels = [f"{row['family']}\n{row['scenario']}" for row in family_scenarios]
    values = [float(row["max_rel_ppm"]) for row in family_scenarios]
    li_values = [float(row["li_inverse_max_rel_ppm"]) for row in family_scenarios]
    x_positions = list(range(len(family_scenarios)))
    width = 0.4
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar([x - width / 2 for x in x_positions], values, width=width, label="scenario", color="#c92a2a")
    ax.bar([x + width / 2 for x in x_positions], li_values, width=width, label="li_inverse_seed", color="#0b7285")
    ax.set_title(title)
    ax.set_ylabel("max seed ppm")
    ax.set_xticks(x_positions, labels, rotation=45, ha="right")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _plot_anchor_summary(
    anchor_rows: list[dict[str, int | str | float | bool]],
    output_path: Path,
) -> None:
    grouped: dict[str, list[dict[str, int | str | float | bool]]] = {}
    for row in anchor_rows:
        grouped.setdefault(str(row["scenario"]), []).append(row)
    fig, ax = plt.subplots(figsize=(10, 6))
    for scenario in SCENARIO_ORDER:
        group = sorted(grouped[scenario], key=lambda row: int(row["n"]))
        ax.plot(
            [int(row["n"]) for row in group],
            [float(row["seed_rel_ppm"]) for row in group],
            marker="o",
            linewidth=2,
            label=scenario,
        )
    li_group = sorted(grouped["baseline"], key=lambda row: int(row["n"]))
    ax.plot(
        [int(row["n"]) for row in li_group],
        [float(row["li_inverse_rel_ppm"]) for row in li_group],
        marker="s",
        linewidth=2,
        color="#0b7285",
        label="li_inverse_seed",
    )
    ax.set_xscale("log")
    ax.set_title("Official exact anchors: sensitivity scenarios versus li_inverse_seed")
    ax.set_xlabel("n")
    ax.set_ylabel("seed ppm")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def build_readme_text(
    family_summary_rows: list[dict[str, int | str | float | bool]],
) -> str:
    exact_rows = [row for row in family_summary_rows if bool(row["exact_labels"])]
    exact_wins = [row for row in exact_rows if bool(row["wins_vs_li_on_max"])]
    exact_total = len(exact_rows)
    exact_baseline_rows = [row for row in exact_rows if str(row["scenario"]) == "baseline"]
    exact_perturbed_rows = [row for row in exact_rows if str(row["scenario"]) != "baseline"]
    exact_unchanged = all(
        float(row["max_rel_ppm"]) == float(
            next(
                base["max_rel_ppm"]
                for base in exact_baseline_rows
                if str(base["dataset"]) == str(row["dataset"]) and str(base["family"]) == str(row["family"])
            )
        )
        for row in exact_perturbed_rows
    )
    local_rows = [row for row in family_summary_rows if not bool(row["exact_labels"])]
    local_all_lose = all(not bool(row["wins_vs_li_on_max"]) for row in local_rows)
    if exact_total and len(exact_wins) == exact_total:
        headline = "the shipped launch advantage is robust on the exact held-out surfaces tested"
    elif exact_wins:
        headline = "the exact held-out evidence is mixed and does not support a robustness claim"
    else:
        headline = "the shipped launch advantage degrades materially under small perturbation"

    lines = [
        "# R-Inverse Sensitivity Probe",
        "",
        "This artifact tests calibration-robustness for the shipped `r_inverse_seed` launch path.",
        "",
        "It perturbs the repacked launch correction terms one at a time by `-10%` and `+10%`, keeps the Newton loop fixed, and compares each scenario against `li_inverse_seed`.",
        "",
        "## Strongest Finding",
        "",
        f"`{headline}`",
        "",
        f"Across the tested exact family cells, `{len(exact_wins)}` of `{exact_total}` scenario summaries still beat `li_inverse_seed` on worst-case seed ppm.",
    ]
    if exact_unchanged:
        lines.extend(
            [
                "",
                "The `-10%` and `+10%` one-at-a-time perturbations did not change the exact family-summary maxima in this run.",
            ]
        )
    if local_rows and local_all_lose:
        lines.extend(
            [
                "",
                "On local `stage_c`, the same perturbations remain diagnostic only and the summary still does not favor `r_inverse_seed` over `li_inverse_seed`.",
            ]
        )
    lines.extend(
        [
            "",
            "The headline exact evidence uses only:",
            "",
            "- the official exact anchor suite through `10^18`",
            "- reproducible exact `stage_a`",
            "- reproducible exact `stage_b`",
            "",
            "The local `stage_c` continuation is included only as a diagnostic appendix and is not used as headline exact evidence.",
            "",
            "## Artifacts",
            "",
            "- [rowwise_results.csv](./rowwise_results.csv)",
            "- [family_summary.csv](./family_summary.csv)",
            "- [anchor_summary.csv](./anchor_summary.csv)",
            "- [plots/exact_family_max_ppm.png](./plots/exact_family_max_ppm.png)",
            "- [plots/local_stage_c_family_max_ppm.png](./plots/local_stage_c_family_max_ppm.png)",
            "- [plots/exact_anchor_sensitivity.png](./plots/exact_anchor_sensitivity.png)",
        ]
    )
    return "\n".join(lines) + "\n"


def write_sensitivity_artifacts(repo_root: Path = REPO_ROOT) -> dict[str, Path]:
    output_dir = repo_root / "benchmarks" / "r_inverse_sensitivity"
    plots_dir = output_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    dataset_rows = load_sensitivity_datasets()
    result_rows = build_sensitivity_result_rows(dataset_rows)
    family_summary_rows = summarize_family_results(result_rows)
    anchor_rows = build_anchor_summary(result_rows)

    rowwise_path = output_dir / "rowwise_results.csv"
    family_summary_path = output_dir / "family_summary.csv"
    anchor_summary_path = output_dir / "anchor_summary.csv"
    readme_path = output_dir / "README.md"

    _write_csv(
        rowwise_path,
        result_rows,
        [
            "dataset",
            "source_label",
            "exact_labels",
            "row_id",
            "family",
            "decade_exponent",
            "n",
            "p_n",
            "scenario",
            "scenario_label",
            "c_scale",
            "kappa_scale",
            "launch_seed",
            "seed",
            "seed_signed_error",
            "seed_absolute_error",
            "seed_rel_ppm",
            "li_inverse_seed",
            "li_inverse_signed_error",
            "li_inverse_absolute_error",
            "li_inverse_rel_ppm",
            "advantage_vs_li_ppm",
        ],
    )
    _write_csv(
        family_summary_path,
        family_summary_rows,
        [
            "dataset",
            "source_label",
            "exact_labels",
            "family",
            "scenario",
            "scenario_label",
            "c_scale",
            "kappa_scale",
            "row_count",
            "max_rel_ppm",
            "mean_rel_ppm",
            "median_rel_ppm",
            "li_inverse_max_rel_ppm",
            "li_inverse_mean_rel_ppm",
            "li_inverse_median_rel_ppm",
            "wins_vs_li_on_max",
            "wins_vs_li_on_mean",
        ],
    )
    _write_csv(
        anchor_summary_path,
        anchor_rows,
        [
            "dataset",
            "source_label",
            "exact_labels",
            "row_id",
            "family",
            "decade_exponent",
            "n",
            "p_n",
            "scenario",
            "scenario_label",
            "c_scale",
            "kappa_scale",
            "launch_seed",
            "seed",
            "seed_signed_error",
            "seed_absolute_error",
            "seed_rel_ppm",
            "li_inverse_seed",
            "li_inverse_signed_error",
            "li_inverse_absolute_error",
            "li_inverse_rel_ppm",
            "advantage_vs_li_ppm",
        ],
    )

    _plot_family_summary(
        family_summary_rows,
        datasets=[ANCHOR_DATASET, "reproducible_exact_stage_a", "reproducible_exact_stage_b"],
        output_path=plots_dir / "exact_family_max_ppm.png",
        title="Exact sensitivity families: scenario max ppm versus li_inverse_seed",
    )
    _plot_family_summary(
        family_summary_rows,
        datasets=["local_continuation_stage_c"],
        output_path=plots_dir / "local_stage_c_family_max_ppm.png",
        title="Local stage_c diagnostic: scenario max ppm versus li_inverse_seed",
    )
    _plot_anchor_summary(anchor_rows, plots_dir / "exact_anchor_sensitivity.png")

    readme_path.write_text(build_readme_text(family_summary_rows), encoding="utf-8", newline="\n")

    return {
        "rowwise": rowwise_path,
        "family_summary": family_summary_path,
        "anchor_summary": anchor_summary_path,
        "readme": readme_path,
        "exact_plot": plots_dir / "exact_family_max_ppm.png",
        "local_plot": plots_dir / "local_stage_c_family_max_ppm.png",
        "anchor_plot": plots_dir / "exact_anchor_sensitivity.png",
    }
