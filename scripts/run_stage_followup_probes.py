from __future__ import annotations

import csv
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_SRC = REPO_ROOT / "src" / "python"
OUTPUT_DIR = REPO_ROOT / "benchmarks" / "stage_followup_probe"
Z5D_CLI = Path(
    "/Users/velocityworks/IdeaProjects/archive/z5d-prime-predictor/src/c/z5d-predictor-c/bin/z5d_cli"
)
PREDICTED_PRIME_PATTERN = re.compile(r"Predicted prime:\s*([0-9]+)")

if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from lpp.off_lattice_benchmark import _li_inverse_seed
from lpp.predictor import _KNOWN_PRIMES, lpp_refined_predictor, lpp_seed


def _require_z5d_cli() -> None:
    if not Z5D_CLI.exists():
        raise SystemExit(f"missing Z5D CLI at {Z5D_CLI}")


def _predict_with_z5d(n_value: int) -> int:
    result = subprocess.run(
        [str(Z5D_CLI), str(n_value)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or result.stdout.strip())
    match = PREDICTED_PRIME_PATTERN.search(result.stdout)
    if match is None:
        raise SystemExit(f"could not parse predicted prime for n={n_value}: {result.stdout.strip()}")
    return int(match.group(1))


def _load_dataset_rows(path: Path, stage_name: str, dataset_variant: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            n_value = int(row["n"])
            rows.append(
                {
                    "row_id": row["row_id"],
                    "stage": stage_name,
                    "dataset_variant": dataset_variant,
                    "family": row["family"],
                    "decade_exponent": int(row["decade_exponent"]),
                    "n": n_value,
                    "p_n": int(row["p_n"]),
                    "regime": "anchor" if _is_power_of_ten(n_value) else "off_anchor",
                }
            )
    return rows


def _is_power_of_ten(value: int) -> bool:
    if value < 1:
        return False
    while value % 10 == 0:
        value //= 10
    return value == 1


def _compute_result_rows(
    rows: list[dict[str, object]],
    *,
    label_override: dict[int, int] | None = None,
    dataset_variant: str | None = None,
) -> list[dict[str, object]]:
    result_rows: list[dict[str, object]] = []
    for row in rows:
        n_value = int(row["n"])
        p_n = (
            int(label_override[n_value])
            if label_override is not None
            else int(row["p_n"])
        )
        lpp_seed_value = lpp_seed(n_value)
        lpp_refined_value = lpp_refined_predictor(n_value)
        li_inverse_value = _li_inverse_seed(n_value)
        for comparator_name, predicted in (
            ("lpp_seed", lpp_seed_value),
            ("lpp_refined_predictor", lpp_refined_value),
            ("li_inverse_seed", li_inverse_value),
        ):
            absolute_error = abs(predicted - p_n)
            result_rows.append(
                {
                    "row_id": row["row_id"],
                    "stage": row["stage"],
                    "dataset_variant": dataset_variant or row["dataset_variant"],
                    "family": row["family"],
                    "regime": row["regime"],
                    "n": n_value,
                    "label_p_n": p_n,
                    "comparator": comparator_name,
                    "predicted": predicted,
                    "signed_error": predicted - p_n,
                    "absolute_error": absolute_error,
                    "rel_ppm": absolute_error / p_n * 1e6,
                }
            )
    return result_rows


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _summarize_by_keys(
    rows: list[dict[str, object]],
    group_keys: tuple[str, ...],
) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)

    summary_rows: list[dict[str, object]] = []
    for key in sorted(grouped.keys()):
        group_rows = grouped[key]
        ppm_values = [float(row["rel_ppm"]) for row in group_rows]
        absolute_values = [int(row["absolute_error"]) for row in group_rows]
        summary_row = {group_key: key[index] for index, group_key in enumerate(group_keys)}
        summary_row.update(
            {
                "row_count": len(group_rows),
                "max_rel_ppm": max(ppm_values),
                "mean_rel_ppm": statistics.fmean(ppm_values),
                "median_rel_ppm": statistics.median(ppm_values),
                "max_absolute_error": max(absolute_values),
                "median_absolute_error": statistics.median(absolute_values),
            }
        )
        summary_rows.append(summary_row)
    return summary_rows


def _build_stage_b_z5d_labels(rows: list[dict[str, object]]) -> dict[int, int]:
    unique_n_values = sorted({int(row["n"]) for row in rows})
    return {n_value: _predict_with_z5d(n_value) for n_value in unique_n_values}


def _write_stage_c_anchor_exact_audit() -> list[dict[str, object]]:
    anchor_rows: list[dict[str, object]] = []
    for n_value in (10**17, 10**18):
        exact_p_n = int(_KNOWN_PRIMES[n_value])
        z5d_label = _predict_with_z5d(n_value)
        lpp_seed_value = lpp_seed(n_value)
        lpp_refined_value = lpp_refined_predictor(n_value)
        li_inverse_value = _li_inverse_seed(n_value)
        anchor_rows.append(
            {
                "n": n_value,
                "exact_p_n": exact_p_n,
                "z5d_label": z5d_label,
                "z5d_minus_exact": z5d_label - exact_p_n,
                "lpp_seed": lpp_seed_value,
                "lpp_seed_minus_exact": lpp_seed_value - exact_p_n,
                "lpp_seed_rel_ppm_exact": abs(lpp_seed_value - exact_p_n) / exact_p_n * 1e6,
                "lpp_refined_predictor": lpp_refined_value,
                "lpp_refined_minus_exact": lpp_refined_value - exact_p_n,
                "lpp_refined_rel_ppm_exact": abs(lpp_refined_value - exact_p_n) / exact_p_n * 1e6,
                "li_inverse_seed": li_inverse_value,
                "li_inverse_minus_exact": li_inverse_value - exact_p_n,
                "li_inverse_rel_ppm_exact": abs(li_inverse_value - exact_p_n) / exact_p_n * 1e6,
            }
        )
    _write_csv(
        OUTPUT_DIR / "stage_c_anchor_exact_audit.csv",
        anchor_rows,
        [
            "n",
            "exact_p_n",
            "z5d_label",
            "z5d_minus_exact",
            "lpp_seed",
            "lpp_seed_minus_exact",
            "lpp_seed_rel_ppm_exact",
            "lpp_refined_predictor",
            "lpp_refined_minus_exact",
            "lpp_refined_rel_ppm_exact",
            "li_inverse_seed",
            "li_inverse_minus_exact",
            "li_inverse_rel_ppm_exact",
        ],
    )
    return anchor_rows


def _write_stage_c_refined_mismatch_rows(stage_c_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    mismatch_rows: list[dict[str, object]] = []
    for row in stage_c_rows:
        n_value = int(row["n"])
        label_p_n = int(row["p_n"])
        refined = lpp_refined_predictor(n_value)
        if refined == label_p_n:
            continue
        seed = lpp_seed(n_value)
        li_inverse = _li_inverse_seed(n_value)
        mismatch_rows.append(
            {
                "row_id": row["row_id"],
                "family": row["family"],
                "regime": row["regime"],
                "n": n_value,
                "z5d_label": label_p_n,
                "lpp_seed": seed,
                "lpp_seed_signed_error": seed - label_p_n,
                "lpp_refined_predictor": refined,
                "lpp_refined_signed_error": refined - label_p_n,
                "li_inverse_seed": li_inverse,
                "li_inverse_signed_error": li_inverse - label_p_n,
                "lpp_refined_absolute_error": abs(refined - label_p_n),
            }
        )
    _write_csv(
        OUTPUT_DIR / "stage_c_refined_mismatch_rows.csv",
        mismatch_rows,
        [
            "row_id",
            "family",
            "regime",
            "n",
            "z5d_label",
            "lpp_seed",
            "lpp_seed_signed_error",
            "lpp_refined_predictor",
            "lpp_refined_signed_error",
            "lpp_refined_absolute_error",
            "li_inverse_seed",
            "li_inverse_signed_error",
        ],
    )
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in mismatch_rows:
        grouped[(str(row["family"]), str(row["regime"]))].append(row)
    summary_rows: list[dict[str, object]] = []
    for key in sorted(grouped.keys()):
        group_rows = grouped[key]
        absolute_errors = [int(row["lpp_refined_absolute_error"]) for row in group_rows]
        summary_rows.append(
            {
                "family": key[0],
                "regime": key[1],
                "row_count": len(group_rows),
                "max_absolute_error": max(absolute_errors),
                "mean_absolute_error": statistics.fmean(absolute_errors),
                "median_absolute_error": statistics.median(absolute_errors),
            }
        )
    _write_csv(
        OUTPUT_DIR / "stage_c_refined_mismatch_summary.csv",
        summary_rows,
        [
            "family",
            "regime",
            "row_count",
            "max_absolute_error",
            "mean_absolute_error",
            "median_absolute_error",
        ],
    )
    return mismatch_rows


def _plot_stage_b_label_source_flip(summary_rows: list[dict[str, object]]) -> None:
    exact_lookup = {
        row["family"]: row
        for row in summary_rows
        if row["dataset_variant"] == "stage_b_exact"
        and row["regime"] == "off_anchor"
        and row["comparator"] == "lpp_seed"
    }
    z5d_lookup = {
        row["family"]: row
        for row in summary_rows
        if row["dataset_variant"] == "stage_b_z5d_relabel"
        and row["regime"] == "off_anchor"
        and row["comparator"] == "lpp_seed"
    }
    family_keys = ["boundary_window", "dense_local_window", "off_lattice_decimal"]
    family_labels = ["boundary", "dense local", "off lattice"]
    xs = range(len(family_keys))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    ax = axes[0]
    ax.plot(
        xs,
        [exact_lookup[key]["max_rel_ppm"] for key in family_keys],
        marker="o",
        color="#1f77b4",
        label="Stage B exact LPP",
    )
    ax.plot(
        xs,
        [
            next(
                row["max_rel_ppm"]
                for row in summary_rows
                if row["dataset_variant"] == "stage_b_exact"
                and row["regime"] == "off_anchor"
                and row["family"] == key
                and row["comparator"] == "li_inverse_seed"
            )
            for key in family_keys
        ],
        marker="s",
        color="#ff7f0e",
        label="Stage B exact li^-1",
    )
    ax.plot(
        xs,
        [z5d_lookup[key]["max_rel_ppm"] for key in family_keys],
        marker="o",
        color="#2ca02c",
        label="Stage B z5d relabel LPP",
    )
    ax.plot(
        xs,
        [
            next(
                row["max_rel_ppm"]
                for row in summary_rows
                if row["dataset_variant"] == "stage_b_z5d_relabel"
                and row["regime"] == "off_anchor"
                and row["family"] == key
                and row["comparator"] == "li_inverse_seed"
            )
            for key in family_keys
        ],
        marker="s",
        color="#d62728",
        label="Stage B z5d relabel li^-1",
    )
    ax.set_yscale("log")
    ax.set_xticks(list(xs), family_labels)
    ax.set_ylabel("Worst-case seed ppm")
    ax.set_title("Same Stage B indices, different labels")
    ax.grid(True, which="both", axis="y", alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[1]
    width = 0.34
    exact_match_rates = []
    median_abs_errors = []
    relabel_rows = _read_csv(OUTPUT_DIR / "stage_b_z5d_relabel_full_rows.csv")
    for key in family_keys:
        z5d_rows = [
            row
            for row in relabel_rows
            if row["family"] == key
            and row["regime"] == "off_anchor"
            and row["comparator"] == "lpp_refined_predictor"
        ]
        exact_match_rates.append(
            100.0
            * statistics.fmean(1.0 if int(row["absolute_error"]) == 0 else 0.0 for row in z5d_rows)
        )
        lpp_rows = [
            row
            for row in relabel_rows
            if row["family"] == key
            and row["regime"] == "off_anchor"
            and row["comparator"] == "lpp_seed"
        ]
        median_abs_errors.append(statistics.median(int(row["absolute_error"]) for row in lpp_rows))
    ax.bar(
        [x - width / 2 for x in xs],
        exact_match_rates,
        width=width,
        color="#2ca02c",
        label="lpp_refined exact-match rate to z5d relabel",
    )
    ax.bar(
        [x + width / 2 for x in xs],
        median_abs_errors,
        width=width,
        color="#9467bd",
        label="Median |lpp_seed - z5d label|",
    )
    ax.set_xticks(list(xs), family_labels)
    ax.set_ylabel("Percent or integer count")
    ax.set_title("What the relabel aligns with")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(fontsize=8)

    fig.suptitle("Stage B label-source flip probe", fontsize=14)
    fig.savefig(OUTPUT_DIR / "stage_b_label_source_flip.png", dpi=180)
    plt.close(fig)


def _plot_stage_regime_split(summary_rows: list[dict[str, object]]) -> None:
    variants = ["baseline_exact", "stage_a_exact", "stage_b_exact", "stage_b_z5d_relabel", "stage_c_local"]
    variant_labels = ["baseline", "stage_a", "stage_b", "stage_b z5d", "stage_c local"]
    regime_colors = {"anchor": "#1f77b4", "off_anchor": "#2ca02c"}

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    for comparator_name, ax, title in (
        ("lpp_seed", axes[0], "LPP mean ppm by regime"),
        ("li_inverse_seed", axes[1], "li^-1 mean ppm by regime"),
    ):
        anchor_values = []
        off_anchor_values = []
        for variant in variants:
            variant_rows = [
                row
                for row in summary_rows
                if row["dataset_variant"] == variant
                and row["family"] == "all_families"
                and row["comparator"] == comparator_name
            ]
            anchor_row = next(row for row in variant_rows if row["regime"] == "anchor")
            off_anchor_row = next(row for row in variant_rows if row["regime"] == "off_anchor")
            anchor_values.append(anchor_row["mean_rel_ppm"])
            off_anchor_values.append(off_anchor_row["mean_rel_ppm"])
        xs = list(range(len(variants)))
        width = 0.36
        ax.bar([x - width / 2 for x in xs], anchor_values, width=width, color=regime_colors["anchor"], label="anchor")
        ax.bar([x + width / 2 for x in xs], off_anchor_values, width=width, color=regime_colors["off_anchor"], label="off_anchor")
        ax.set_yscale("log")
        ax.set_xticks(xs, variant_labels, rotation=20, ha="right")
        ax.set_ylabel("Mean seed ppm")
        ax.set_title(title)
        ax.grid(True, which="both", axis="y", alpha=0.25)
        ax.legend(fontsize=8)
    fig.suptitle("Anchor versus off-anchor split", fontsize=14)
    fig.savefig(OUTPUT_DIR / "stage_anchor_off_anchor_split.png", dpi=180)
    plt.close(fig)


def _plot_stage_c_mismatch_counts(mismatch_rows: list[dict[str, object]]) -> None:
    family_order = ["boundary_window", "dense_local_window", "off_lattice_decimal"]
    family_labels = ["boundary", "dense local", "off lattice"]
    counts = []
    max_abs_errors = []
    for family in family_order:
        family_rows = [row for row in mismatch_rows if row["family"] == family]
        counts.append(len(family_rows))
        max_abs_errors.append(max(abs(int(row["lpp_refined_signed_error"])) for row in family_rows) if family_rows else 0)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), constrained_layout=True)
    axes[0].bar(family_labels, counts, color="#d62728")
    axes[0].set_title("Stage C refined mismatches by family")
    axes[0].set_ylabel("Row count")
    axes[0].grid(True, axis="y", alpha=0.25)

    axes[1].bar(family_labels, max_abs_errors, color="#9467bd")
    axes[1].set_title("Max |refined - z5d| on mismatch rows")
    axes[1].set_ylabel("Integer count")
    axes[1].grid(True, axis="y", alpha=0.25)

    fig.savefig(OUTPUT_DIR / "stage_c_refined_mismatch_counts.png", dpi=180)
    plt.close(fig)


def _read_csv(path: Path) -> list[dict[str, object]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    _require_z5d_cli()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline_rows = _load_dataset_rows(REPO_ROOT / "data" / "held_out_exact_primes_1e4_1e12.csv", "baseline", "baseline_exact")
    stage_a_rows = _load_dataset_rows(REPO_ROOT / "data" / "held_out_exact_primes_1e13_1e14.csv", "stage_a", "stage_a_exact")
    stage_b_rows = _load_dataset_rows(REPO_ROOT / "data" / "held_out_exact_primes_1e15_1e16.csv", "stage_b", "stage_b_exact")
    stage_c_rows = _load_dataset_rows(REPO_ROOT / "data" / "held_out_z5d_primes_1e17_1e18.csv", "stage_c", "stage_c_local")

    stage_b_z5d_labels = _build_stage_b_z5d_labels(stage_b_rows)

    full_result_rows = []
    full_result_rows.extend(_compute_result_rows(baseline_rows))
    full_result_rows.extend(_compute_result_rows(stage_a_rows))
    full_result_rows.extend(_compute_result_rows(stage_b_rows))
    stage_b_z5d_rows = _compute_result_rows(stage_b_rows, label_override=stage_b_z5d_labels, dataset_variant="stage_b_z5d_relabel")
    full_result_rows.extend(stage_b_z5d_rows)
    full_result_rows.extend(_compute_result_rows(stage_c_rows))

    _write_csv(
        OUTPUT_DIR / "all_probe_rows.csv",
        full_result_rows,
        [
            "row_id",
            "stage",
            "dataset_variant",
            "family",
            "regime",
            "n",
            "label_p_n",
            "comparator",
            "predicted",
            "signed_error",
            "absolute_error",
            "rel_ppm",
        ],
    )
    _write_csv(
        OUTPUT_DIR / "stage_b_z5d_relabel_full_rows.csv",
        stage_b_z5d_rows,
        [
            "row_id",
            "stage",
            "dataset_variant",
            "family",
            "regime",
            "n",
            "label_p_n",
            "comparator",
            "predicted",
            "signed_error",
            "absolute_error",
            "rel_ppm",
        ],
    )

    family_summary_rows = _summarize_by_keys(
        full_result_rows,
        ("dataset_variant", "family", "regime", "comparator"),
    )
    _write_csv(
        OUTPUT_DIR / "family_regime_summary.csv",
        family_summary_rows,
        [
            "dataset_variant",
            "family",
            "regime",
            "comparator",
            "row_count",
            "max_rel_ppm",
            "mean_rel_ppm",
            "median_rel_ppm",
            "max_absolute_error",
            "median_absolute_error",
        ],
    )

    stage_regime_rows: list[dict[str, object]] = []
    grouped_stage_rows: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in full_result_rows:
        grouped_stage_rows[(str(row["dataset_variant"]), str(row["regime"]), str(row["comparator"]))].append(row)
    for key in sorted(grouped_stage_rows.keys()):
        dataset_variant, regime, comparator = key
        group_rows = grouped_stage_rows[key]
        ppm_values = [float(row["rel_ppm"]) for row in group_rows]
        absolute_values = [int(row["absolute_error"]) for row in group_rows]
        stage_regime_rows.append(
            {
                "dataset_variant": dataset_variant,
                "family": "all_families",
                "regime": regime,
                "comparator": comparator,
                "row_count": len(group_rows),
                "max_rel_ppm": max(ppm_values),
                "mean_rel_ppm": statistics.fmean(ppm_values),
                "median_rel_ppm": statistics.median(ppm_values),
                "max_absolute_error": max(absolute_values),
                "median_absolute_error": statistics.median(absolute_values),
            }
        )
    _write_csv(
        OUTPUT_DIR / "stage_regime_summary.csv",
        stage_regime_rows,
        [
            "dataset_variant",
            "family",
            "regime",
            "comparator",
            "row_count",
            "max_rel_ppm",
            "mean_rel_ppm",
            "median_rel_ppm",
            "max_absolute_error",
            "median_absolute_error",
        ],
    )

    _write_stage_c_anchor_exact_audit()
    mismatch_rows = _write_stage_c_refined_mismatch_rows(stage_c_rows)

    _plot_stage_b_label_source_flip(family_summary_rows)
    _plot_stage_regime_split(stage_regime_rows)
    _plot_stage_c_mismatch_counts(mismatch_rows)

    print(OUTPUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
