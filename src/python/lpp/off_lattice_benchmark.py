from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

import gmpy2 as gp
import mpmath as mp

from .predictor import lpp_seed


MIN_DECADE_EXPONENT = 4
MAX_DECADE_EXPONENT = 12
BOUNDARY_WINDOW_RADIUS = 128
DENSE_LOCAL_WINDOW_LENGTH = 1024

HELD_OUT_DATASET = "held_out_exact_primes_1e4_1e12.csv"
HELD_OUT_MANIFEST = "held_out_exact_primes_1e4_1e12_manifest.json"
OFF_LATTICE_CSV = "off_lattice_benchmark.csv"
OFF_LATTICE_SUMMARY = "off_lattice_benchmark_summary.json"
OFF_LATTICE_REPORT = "off_lattice_benchmark.md"

SCALING_STAGE_SPECS = [
    {
        "name": "baseline",
        "label": r"$10^4 \ldots 10^{12}$",
        "dataset": HELD_OUT_DATASET,
        "manifest": HELD_OUT_MANIFEST,
        "source_label": "published exact",
        "exact_labels": True,
        "min_exponent": 4,
        "max_exponent": 12,
        "include_dense_local_window": False,
        "classification_stage": False,
    },
    {
        "name": "stage_a",
        "label": r"$10^{13} \ldots 10^{14}$",
        "dataset": "held_out_exact_primes_1e13_1e14.csv",
        "manifest": "held_out_exact_primes_1e13_1e14_manifest.json",
        "source_label": "reproducible exact",
        "exact_labels": True,
        "min_exponent": 13,
        "max_exponent": 14,
        "include_dense_local_window": True,
        "classification_stage": True,
    },
    {
        "name": "stage_b",
        "label": r"$10^{15} \ldots 10^{16}$",
        "dataset": "held_out_exact_primes_1e15_1e16.csv",
        "manifest": "held_out_exact_primes_1e15_1e16_manifest.json",
        "source_label": "reproducible exact",
        "exact_labels": True,
        "min_exponent": 15,
        "max_exponent": 16,
        "include_dense_local_window": True,
        "classification_stage": True,
    },
    {
        "name": "stage_c",
        "label": r"$10^{17} \ldots 10^{18}$ (local continuation)",
        "dataset": "held_out_z5d_primes_1e17_1e18.csv",
        "manifest": "held_out_z5d_primes_1e17_1e18_manifest.json",
        "source_label": "local continuation",
        "exact_labels": False,
        "min_exponent": 17,
        "max_exponent": 18,
        "include_dense_local_window": True,
        "classification_stage": True,
    },
]

COMPARATOR_SPECS = [
    {
        "name": "pnt_first_order",
        "formula": r"n \log n",
        "description": "First-order PNT inversion.",
    },
    {
        "name": "pnt_two_term",
        "formula": r"n(\log n + \log\log n - 1)",
        "description": "Two-term PNT correction.",
    },
    {
        "name": "cipolla_one_over_log",
        "formula": r"n(\log n + \log\log n - 1 + (\log\log n - 2)/\log n)",
        "description": "Cipolla truncation through the 1/log term.",
    },
    {
        "name": "cipolla_one_over_log_sq",
        "formula": r"n(\log n + \log\log n - 1 + (\log\log n - 2)/\log n - ((\log\log n)^2 - 6\log\log n + 11)/(2\log^2 n))",
        "description": "Classical Cipolla truncation through the 1/log^2 term.",
    },
    {
        "name": "li_inverse_seed",
        "formula": r"li^{-1}(n)",
        "description": "Numerical inverse-log-integral seed.",
    },
    {
        "name": "axler_three_term_point_estimate",
        "formula": r"n(\log n + \log\log n - 1 + (\log\log n - 2)/\log n - ((\log\log n)^2 - 6\log\log n + 11)/(2\log^2 n) + ((\log\log n)^3 - 9(\log\log n)^2 + 23\log\log n - 11)/(6\log^3 n))",
        "description": "Third-order asymptotic point estimate following Axler-era explicit nth-prime expansions.",
    },
    {
        "name": "lpp_seed",
        "formula": r"round(P(n) + d(n) + e(n))",
        "description": "Lorentz Prime Predictor seed.",
    },
]

SUMMARY_METRICS = (
    "mean_signed_error",
    "mean_absolute_error",
    "mean_ppm",
    "median_ppm",
    "max_ppm",
    "rms_ppm",
    "sign_ratio",
)


def get_stage_spec(stage_name: str) -> dict[str, object]:
    for spec in SCALING_STAGE_SPECS:
        if str(spec["name"]) == stage_name:
            return spec
    raise ValueError(f"unknown stage: {stage_name}")


def declared_stage_names(include_baseline: bool = True) -> list[str]:
    return [
        str(spec["name"])
        for spec in SCALING_STAGE_SPECS
        if include_baseline or str(spec["name"]) != "baseline"
    ]


def classification_stage_names() -> list[str]:
    return [str(spec["name"]) for spec in SCALING_STAGE_SPECS if bool(spec["classification_stage"])]


def exact_stage_names() -> list[str]:
    return [str(spec["name"]) for spec in SCALING_STAGE_SPECS if bool(spec["exact_labels"])]


def stage_name_for_exponent(exponent: int) -> str:
    for spec in SCALING_STAGE_SPECS:
        if int(spec["min_exponent"]) <= exponent <= int(spec["max_exponent"]):
            return str(spec["name"])
    raise ValueError(f"no declared stage for exponent {exponent}")


def build_exact_specs(
    min_exponent: int,
    max_exponent: int,
    *,
    include_dense_local_window: bool,
) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for exponent in range(min_exponent, max_exponent + 1):
        base = 10**exponent
        for multiplier in range(2, 10):
            n_value = multiplier * base
            rows.append(
                {
                    "row_id": f"off_lattice_decimal__k{exponent}__m{multiplier}",
                    "family": "off_lattice_decimal",
                    "decade_exponent": exponent,
                    "n": n_value,
                }
            )
        for offset in range(-BOUNDARY_WINDOW_RADIUS, BOUNDARY_WINDOW_RADIUS + 1):
            n_value = base + offset
            rows.append(
                {
                    "row_id": f"boundary_window__k{exponent}__offset{offset:+d}",
                    "family": "boundary_window",
                    "decade_exponent": exponent,
                    "n": n_value,
                }
            )
        if include_dense_local_window:
            dense_intervals = [
                ("lower", base - DENSE_LOCAL_WINDOW_LENGTH, base - 1),
                ("middle", 5 * (10 ** (exponent - 1)), 5 * (10 ** (exponent - 1)) + DENSE_LOCAL_WINDOW_LENGTH - 1),
                ("upper", 9 * (10 ** (exponent - 1)), 9 * (10 ** (exponent - 1)) + DENSE_LOCAL_WINDOW_LENGTH - 1),
            ]
            for window_name, start_n, end_n in dense_intervals:
                for n_value in range(start_n, end_n + 1):
                    offset = n_value - start_n
                    rows.append(
                        {
                            "row_id": f"dense_local_window__k{exponent}__{window_name}__offset{offset:+d}",
                            "family": "dense_local_window",
                            "decade_exponent": exponent,
                            "n": n_value,
                        }
                    )
    rows.sort(key=lambda row: (int(row["n"]), str(row["family"]), str(row["row_id"])))
    return rows


def build_held_out_specs() -> list[dict[str, int | str]]:
    return build_exact_specs(
        MIN_DECADE_EXPONENT,
        MAX_DECADE_EXPONENT,
        include_dense_local_window=False,
    )


def build_stage_specs(stage_name: str) -> list[dict[str, int | str]]:
    spec = get_stage_spec(stage_name)
    return build_exact_specs(
        int(spec["min_exponent"]),
        int(spec["max_exponent"]),
        include_dense_local_window=bool(spec["include_dense_local_window"]),
    )


def expected_row_count_for_stage(stage_name: str) -> int:
    return len(build_stage_specs(stage_name))


def unique_index_runs(rows: list[dict[str, int | str]]) -> list[dict[str, object]]:
    unique_n_values = sorted({int(row["n"]) for row in rows})
    if not unique_n_values:
        return []
    runs: list[dict[str, object]] = []
    run_values = [unique_n_values[0]]
    for n_value in unique_n_values[1:]:
        if n_value == run_values[-1] + 1:
            run_values.append(n_value)
            continue
        runs.append(
            {
                "start_n": run_values[0],
                "end_n": run_values[-1],
                "length": len(run_values),
                "n_values": list(run_values),
            }
        )
        run_values = [n_value]
    runs.append(
        {
            "start_n": run_values[0],
            "end_n": run_values[-1],
            "length": len(run_values),
            "n_values": list(run_values),
        }
    )
    return runs


def write_held_out_dataset(path: Path, rows: list[dict[str, int | str]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["row_id", "family", "decade_exponent", "n", "p_n"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_held_out_dataset(path: Path) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "row_id": row["row_id"],
                    "family": row["family"],
                    "decade_exponent": int(row["decade_exponent"]),
                    "n": int(row["n"]),
                    "p_n": int(row["p_n"]),
                }
            )
    if not rows:
        raise ValueError(f"no rows found in {path}")
    return rows


def load_declared_datasets(repo_root: Path, stage_names: list[str] | None = None) -> list[dict[str, int | str]]:
    selected_stage_names = stage_names or declared_stage_names(include_baseline=True)
    rows: list[dict[str, int | str]] = []
    for stage_name in selected_stage_names:
        spec = get_stage_spec(stage_name)
        dataset_rows = parse_held_out_dataset(repo_root / "data" / str(spec["dataset"]))
        rows.extend(dataset_rows)
    return rows


def _li_inverse_seed(n_value: int) -> int:
    mp.mp.dps = 100
    ln_n = math.log(n_value)
    ln_ln_n = math.log(ln_n)
    start = n_value * (ln_n + ln_ln_n - 1.0 + (ln_ln_n - 2.0) / ln_n)
    seed = mp.mpf(start)
    target = mp.mpf(n_value)
    for _ in range(8):
        seed -= (mp.li(seed) - target) * mp.log(seed)
    return _round_half_up_positive(seed)


def _round_half_up_positive(value: float | mp.mpf) -> int:
    return int(gp.mpz(value + 0.5))


def compute_seed(comparator_name: str, n_value: int) -> int:
    if comparator_name == "lpp_seed":
        return lpp_seed(n_value)

    ln_n = math.log(n_value)
    ln_ln_n = math.log(ln_n)
    base = ln_n + ln_ln_n - 1.0
    log_term = (ln_ln_n - 2.0) / ln_n
    log_sq_term = ((ln_ln_n * ln_ln_n) - 6.0 * ln_ln_n + 11.0) / (2.0 * ln_n * ln_n)
    log_cu_term = (
        (ln_ln_n**3) - 9.0 * (ln_ln_n**2) + 23.0 * ln_ln_n - 11.0
    ) / (6.0 * (ln_n**3))

    if comparator_name == "pnt_first_order":
        value = n_value * ln_n
    elif comparator_name == "pnt_two_term":
        value = n_value * base
    elif comparator_name == "cipolla_one_over_log":
        value = n_value * (base + log_term)
    elif comparator_name == "cipolla_one_over_log_sq":
        value = n_value * (base + log_term - log_sq_term)
    elif comparator_name == "li_inverse_seed":
        return _li_inverse_seed(n_value)
    elif comparator_name == "axler_three_term_point_estimate":
        value = n_value * (base + log_term - log_sq_term + log_cu_term)
    else:
        raise ValueError(f"unknown comparator: {comparator_name}")

    return _round_half_up_positive(value)


def refine_seed(seed: int) -> int:
    return int(gp.next_prime(seed - 1))


def build_off_lattice_result_rows(dataset_rows: list[dict[str, int | str]]) -> list[dict[str, int | str | float]]:
    results: list[dict[str, int | str | float]] = []
    for row in dataset_rows:
        n_value = int(row["n"])
        p_n = int(row["p_n"])
        stage_name = stage_name_for_exponent(int(row["decade_exponent"]))
        for spec in COMPARATOR_SPECS:
            comparator_name = str(spec["name"])
            seed = compute_seed(comparator_name, n_value)
            refined = refine_seed(seed)
            seed_signed = seed - p_n
            refined_signed = refined - p_n
            seed_abs = abs(seed_signed)
            refined_abs = abs(refined_signed)
            seed_ppm = seed_abs / p_n * 1e6
            refined_ppm = refined_abs / p_n * 1e6
            results.append(
                {
                    "row_id": row["row_id"],
                    "stage": stage_name,
                    "family": row["family"],
                    "decade_exponent": row["decade_exponent"],
                    "n": n_value,
                    "p_n": p_n,
                    "comparator": comparator_name,
                    "seed": seed,
                    "seed_signed_error": seed_signed,
                    "seed_absolute_error": seed_abs,
                    "seed_rel_ppm": seed_ppm,
                    "refined_predictor": refined,
                    "refined_signed_error": refined_signed,
                    "refined_absolute_error": refined_abs,
                    "refined_rel_ppm": refined_ppm,
                }
            )
    return results


def _aggregate_metric_rows(rows: list[dict[str, int | str | float]], ppm_key: str, signed_key: str, abs_key: str) -> dict[str, float]:
    ppm_values = [float(row[ppm_key]) for row in rows]
    signed_values = [float(row[signed_key]) for row in rows]
    abs_values = [float(row[abs_key]) for row in rows]
    sign_ratio = sum(1 for value in signed_values if value > 0) / len(signed_values)
    return {
        "mean_signed_error": statistics.fmean(signed_values),
        "mean_absolute_error": statistics.fmean(abs_values),
        "mean_ppm": statistics.fmean(ppm_values),
        "median_ppm": statistics.median(ppm_values),
        "max_ppm": max(ppm_values),
        "rms_ppm": math.sqrt(statistics.fmean([value * value for value in ppm_values])),
        "sign_ratio": sign_ratio,
    }


def _comparator_summary(rows: list[dict[str, int | str | float]]) -> dict[str, object]:
    summary: dict[str, object] = {}
    for comparator_name in [str(spec["name"]) for spec in COMPARATOR_SPECS]:
        comp_rows = [row for row in rows if row["comparator"] == comparator_name]
        summary[comparator_name] = {
            "seed": _aggregate_metric_rows(comp_rows, "seed_rel_ppm", "seed_signed_error", "seed_absolute_error"),
            "refined": _aggregate_metric_rows(comp_rows, "refined_rel_ppm", "refined_signed_error", "refined_absolute_error"),
        }
    return summary


def _family_summary(rows: list[dict[str, int | str | float]], family_names: list[str]) -> dict[str, object]:
    family_summary: dict[str, object] = {}
    for family in family_names:
        family_rows = [row for row in rows if row["family"] == family]
        if not family_rows:
            continue
        per_decade: dict[str, object] = {}
        decades = sorted({int(row["decade_exponent"]) for row in family_rows})
        for decade in decades:
            decade_rows = [row for row in family_rows if int(row["decade_exponent"]) == decade]
            per_decade[str(decade)] = _comparator_summary(decade_rows)
        family_summary[family] = {
            "comparators": _comparator_summary(family_rows),
            "per_decade": per_decade,
        }
    return family_summary


def _stage_summary(rows: list[dict[str, int | str | float]], family_names: list[str]) -> dict[str, object]:
    return {
        "overall": _comparator_summary(rows),
        "by_family": _family_summary(rows, family_names),
    }


def _best_comparator_for_metric(
    family_comparators: dict[str, object],
    metric_name: str,
    *,
    estimand: str = "seed",
    exclude_lpp: bool = False,
) -> tuple[str, float]:
    items = []
    for comparator_name, metrics in family_comparators.items():
        if exclude_lpp and comparator_name == "lpp_seed":
            continue
        items.append((comparator_name, float(metrics[estimand][metric_name])))
    best_name, best_value = min(items, key=lambda item: (item[1], item[0]))
    return best_name, best_value


def _decision_summary(summary: dict[str, object]) -> dict[str, object]:
    present_stages = set(summary["by_stage"].keys())
    completed_stages = [stage_name for stage_name in classification_stage_names() if stage_name in present_stages]
    decision_cells: list[dict[str, object]] = []
    lpp_mean_wins = 0
    total_cells = 0
    tail_survives = True

    for stage_name in completed_stages:
        stage_family_summary = summary["by_stage"][stage_name]["by_family"]
        for family, family_data in stage_family_summary.items():
            family_comparators = family_data["comparators"]
            lpp_seed_metrics = family_comparators["lpp_seed"]["seed"]
            best_max_name, best_max_value = _best_comparator_for_metric(family_comparators, "max_ppm")
            best_mean_name, best_mean_value = _best_comparator_for_metric(family_comparators, "mean_ppm")
            best_median_name, best_median_value = _best_comparator_for_metric(family_comparators, "median_ppm")
            best_classical_name, best_classical_value = _best_comparator_for_metric(
                family_comparators,
                "max_ppm",
                exclude_lpp=True,
            )
            lpp_is_best_max = best_max_name == "lpp_seed"
            lpp_is_best_mean = best_mean_name == "lpp_seed"
            if not lpp_is_best_max:
                tail_survives = False
            if lpp_is_best_mean:
                lpp_mean_wins += 1
            total_cells += 1
            decision_cells.append(
                {
                    "stage": stage_name,
                    "family": family,
                    "lpp_max_ppm": float(lpp_seed_metrics["max_ppm"]),
                    "lpp_mean_ppm": float(lpp_seed_metrics["mean_ppm"]),
                    "lpp_median_ppm": float(lpp_seed_metrics["median_ppm"]),
                    "best_seed_max_comparator": best_max_name,
                    "best_seed_mean_comparator": best_mean_name,
                    "best_seed_median_comparator": best_median_name,
                    "best_classical_max_comparator": best_classical_name,
                    "best_classical_max_ppm": best_classical_value,
                    "max_ratio_lpp_to_best_classical": float(lpp_seed_metrics["max_ppm"]) / best_classical_value,
                    "mean_ratio_lpp_to_best_seed": float(lpp_seed_metrics["mean_ppm"]) / best_mean_value,
                    "median_ratio_lpp_to_best_seed": float(lpp_seed_metrics["median_ppm"]) / best_median_value,
                    "lpp_is_best_max": lpp_is_best_max,
                    "lpp_is_best_mean": lpp_is_best_mean,
                }
            )

    mean_threshold = math.ceil(total_cells / 2) if total_cells else 0
    if total_cells == 0:
        conclusion = "not evaluated"
    elif tail_survives and lpp_mean_wins >= mean_threshold:
        conclusion = "survives strongly"
    elif tail_survives:
        conclusion = "survives in the tail only"
    else:
        conclusion = "does not survive"

    return {
        "conclusion": conclusion,
        "completed_stages": completed_stages,
        "total_stage_family_cells": total_cells,
        "lpp_mean_wins": lpp_mean_wins,
        "mean_win_threshold": mean_threshold,
        "tail_survives": tail_survives,
        "cells": decision_cells,
    }


def summarize_off_lattice_results(rows: list[dict[str, int | str | float]]) -> dict[str, object]:
    family_names = sorted({str(row["family"]) for row in rows})
    stages = [str(spec["name"]) for spec in SCALING_STAGE_SPECS if any(str(row["stage"]) == str(spec["name"]) for row in rows)]
    summary: dict[str, object] = {
        "families": family_names,
        "comparators": [str(spec["name"]) for spec in COMPARATOR_SPECS],
        "stages": stages,
        "stage_labels": {str(spec["name"]): str(spec["label"]) for spec in SCALING_STAGE_SPECS if str(spec["name"]) in stages},
        "stage_sources": {str(spec["name"]): str(spec["source_label"]) for spec in SCALING_STAGE_SPECS if str(spec["name"]) in stages},
        "exact_stages": [stage_name for stage_name in stages if stage_name in exact_stage_names()],
        "overall": _comparator_summary(rows),
        "by_family": _family_summary(rows, family_names),
        "by_stage": {},
        "cumulative_by_stage": {},
        "decision": {},
        "worst_seed_rows_overall": [],
        "worst_refined_rows_overall": [],
    }

    stage_order = [str(spec["name"]) for spec in SCALING_STAGE_SPECS if str(spec["name"]) in stages]
    cumulative_rows: list[dict[str, int | str | float]] = []
    for stage_name in stage_order:
        stage_rows = [row for row in rows if row["stage"] == stage_name]
        summary["by_stage"][stage_name] = _stage_summary(stage_rows, family_names)
        cumulative_rows.extend(stage_rows)
        summary["cumulative_by_stage"][stage_name] = _stage_summary(cumulative_rows, family_names)

    summary["decision"] = _decision_summary(summary)
    summary["worst_seed_rows_overall"] = sorted(
        rows,
        key=lambda row: (float(row["seed_rel_ppm"]), int(row["n"])),
        reverse=True,
    )[:10]
    summary["worst_refined_rows_overall"] = sorted(
        rows,
        key=lambda row: (float(row["refined_rel_ppm"]), int(row["n"])),
        reverse=True,
    )[:10]
    return summary


def _format_metric(value: float) -> str:
    return f"{value:.6f}"


def _headline_for_conclusion(conclusion: str) -> str:
    if conclusion == "not evaluated":
        return "The scaling classification has not been evaluated yet because no stage datasets beyond the baseline were included in this run."
    if conclusion == "survives strongly":
        return "LPP keeps the best worst-case seed ppm on every declared scaling stage and also wins the average-error criterion often enough to count as a strong survival result."
    if conclusion == "survives in the tail only":
        return "LPP keeps the best worst-case seed ppm on every declared scaling stage, but the average-error advantage is mixed."
    return "LPP loses the worst-case seed ppm lead on at least one declared scaling stage."


def write_off_lattice_benchmark_artifacts(repo_root: Path, stage_names: list[str] | None = None) -> dict[str, Path]:
    dataset_rows = load_declared_datasets(repo_root, stage_names)
    result_rows = build_off_lattice_result_rows(dataset_rows)
    summary = summarize_off_lattice_results(result_rows)

    benchmark_dir = repo_root / "benchmarks"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    csv_path = benchmark_dir / OFF_LATTICE_CSV
    summary_path = benchmark_dir / OFF_LATTICE_SUMMARY
    md_path = benchmark_dir / OFF_LATTICE_REPORT

    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "row_id",
                "family",
                "decade_exponent",
                "n",
                "p_n",
                "comparator",
                "seed",
                "seed_signed_error",
                "seed_absolute_error",
                "seed_rel_ppm",
                "refined_predictor",
                "refined_signed_error",
                "refined_absolute_error",
                "refined_rel_ppm",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in result_rows:
            writer.writerow({key: row[key] for key in writer.fieldnames})

    summary_path.write_text(json.dumps(summary, indent=2) + "\n")

    decision = summary["decision"]
    headline = _headline_for_conclusion(str(decision["conclusion"]))
    stage_labels = [summary["stage_labels"][stage_name] for stage_name in summary["stages"]]
    horizon_text = ", ".join(stage_labels)
    exact_stage_labels = [summary["stage_labels"][stage_name] for stage_name in summary["exact_stages"]]
    exact_horizon_text = ", ".join(exact_stage_labels)
    has_non_exact_stage = len(summary["exact_stages"]) != len(summary["stages"])
    md_lines = [
        "# Off-Lattice Adversarial Benchmark",
        "",
        headline,
        "",
        "## Declared Horizon",
        "",
        f"This benchmark combines the stages currently available in the repository: {horizon_text}.",
        "",
        "Implemented stages:",
        "",
    ]
    for stage_name in summary["stages"]:
        md_lines.append(
            f"- `{stage_name}`: {summary['stage_labels'][stage_name]} from {summary['stage_sources'][stage_name]}"
        )
    md_lines.extend(
        [
            "",
            "Families:",
            "",
            "- `off_lattice_decimal`: $m \\cdot 10^k$ with $m = 2,\\dots,9$",
            "- `boundary_window`: all integers in $[10^k - 128,\\; 10^k + 128]$",
            "- `dense_local_window`: deterministic local sweeps of length $1024$ at lower, middle, and upper locations inside each new stage exponent",
            "",
            "## Mechanical Conclusion",
            "",
            f"Conclusion: `{decision['conclusion']}`.",
            "",
            "| Stage | Family | LPP max ppm | Best classical by max ppm | Classical max ppm | LPP / classical max ratio | Best mean comparator |",
            "| --- | --- | ---: | --- | ---: | ---: | --- |",
        ]
    )
    for cell in decision["cells"]:
        md_lines.append(
            f"| {cell['stage']} | {cell['family']} | {_format_metric(float(cell['lpp_max_ppm']))} | "
            f"{cell['best_classical_max_comparator']} | {_format_metric(float(cell['best_classical_max_ppm']))} | "
            f"{_format_metric(float(cell['max_ratio_lpp_to_best_classical']))} | {cell['best_seed_mean_comparator']} |"
        )
    md_lines.extend(
        [
            "",
            "## Best Seed Max ppm by Stage and Family",
            "",
            "| Stage | Family | Winner | Max ppm |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for stage_name in summary["stages"]:
        stage_summary = summary["by_stage"][stage_name]["by_family"]
        for family, family_data in stage_summary.items():
            winner_name, winner_value = _best_comparator_for_metric(family_data["comparators"], "max_ppm")
            md_lines.append(f"| {stage_name} | {family} | {winner_name} | {_format_metric(winner_value)} |")
    md_lines.extend(
        [
            "",
            "## Best Seed Mean ppm by Stage and Family",
            "",
            "| Stage | Family | Winner | Mean ppm |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for stage_name in summary["stages"]:
        stage_summary = summary["by_stage"][stage_name]["by_family"]
        for family, family_data in stage_summary.items():
            winner_name, winner_value = _best_comparator_for_metric(family_data["comparators"], "mean_ppm")
            md_lines.append(f"| {stage_name} | {family} | {winner_name} | {_format_metric(winner_value)} |")
    md_lines.extend(
        [
            "",
            "## Worst-Case Seed Rows Overall",
            "",
            "| Comparator | Stage | Family | n | Seed ppm | Seed signed error |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["worst_seed_rows_overall"]:
        md_lines.append(
            f"| {row['comparator']} | {row['stage']} | {row['family']} | {row['n']} | {_format_metric(float(row['seed_rel_ppm']))} | {row['seed_signed_error']} |"
        )
    md_lines.extend(
        [
            "",
            "## Visualization Index",
            "",
            "### Stage Seed Max ppm by Family",
            "",
            "This is the lead figure because it answers the scaling question directly in the tail.",
            "",
            "![Stage seed max ppm by family](./plots/off_lattice/stage_seed_max_ppm_by_family.png)",
            "",
            "### Stage Seed Mean ppm by Family",
            "",
            "This shows whether the average-error story matches or diverges from the tail story.",
            "",
            "![Stage seed mean ppm by family](./plots/off_lattice/stage_seed_mean_ppm_by_family.png)",
            "",
            "### LPP vs Best Classical Ratio",
            "",
            "Ratios below $1$ mean LPP is better on that metric in that stage-family cell.",
            "",
            "![LPP versus best classical ratio](./plots/off_lattice/lpp_vs_best_classical_ratio.png)",
            "",
        ]
    )
    for stage_name in decision["completed_stages"]:
        md_lines.extend(
            [
                f"### Boundary Signed Error Heatmap: {stage_name}",
                "",
                f"![Boundary signed seed error {stage_name}](./plots/off_lattice/boundary_window_signed_seed_error_lpp_{stage_name}.png)",
                "",
                f"### Dense Local Window Ranked Seed ppm: {stage_name}",
                "",
                f"![Dense local window ranked seed ppm {stage_name}](./plots/off_lattice/dense_local_window_ranked_seed_ppm_{stage_name}.png)",
                "",
            ]
        )
    md_lines.extend(
        [
            "## Conclusion",
            "",
            headline,
            "",
        ]
    )
    if has_non_exact_stage:
        md_lines.extend(
            [
                "",
                f"The horizon {exact_horizon_text} remains in the reproducible exact class.",
                "",
                "The local stage belongs to the local continuation class rather than the published exact or reproducible exact classes.",
            ]
        )
    else:
        md_lines.extend(
            [
                "",
                "This answer is exact on the committed horizon and says nothing beyond that horizon.",
            ]
        )
    md_path.write_text("\n".join(md_lines) + "\n")
    return {"csv": csv_path, "summary": summary_path, "markdown": md_path}
