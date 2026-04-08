from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lpp.off_lattice_benchmark import (
    COMPARATOR_SPECS,
    build_held_out_specs,
    build_off_lattice_result_rows,
    build_stage_specs,
    expected_row_count_for_stage,
    summarize_off_lattice_results,
    unique_index_runs,
    write_held_out_dataset,
    write_off_lattice_benchmark_artifacts,
)


class OffLatticeBenchmarkTests(unittest.TestCase):
    def test_build_held_out_specs_counts(self) -> None:
        rows = build_held_out_specs()
        self.assertEqual(len(rows), 2385)
        off_lattice = [row for row in rows if row["family"] == "off_lattice_decimal"]
        boundary = [row for row in rows if row["family"] == "boundary_window"]
        self.assertEqual(len(off_lattice), 72)
        self.assertEqual(len(boundary), 2313)
        self.assertEqual(len({str(row["row_id"]) for row in rows}), len(rows))

    def test_build_stage_specs_counts(self) -> None:
        rows = build_stage_specs("stage_a")
        self.assertEqual(len(rows), 6674)
        self.assertEqual(expected_row_count_for_stage("stage_a"), 6674)
        families = {str(row["family"]) for row in rows}
        self.assertEqual(families, {"boundary_window", "dense_local_window", "off_lattice_decimal"})

    def test_unique_index_runs_collapses_dense_and_boundary_ranges(self) -> None:
        rows = build_stage_specs("stage_a")
        runs = unique_index_runs(rows)
        run_lengths = sorted(int(run["length"]) for run in runs)
        self.assertIn(1153, run_lengths)
        self.assertIn(1024, run_lengths)
        self.assertIn(1, run_lengths)

    def test_result_rows_cover_every_comparator(self) -> None:
        dataset_rows = [
            {
                "row_id": "off_lattice_decimal__k4__m2",
                "family": "off_lattice_decimal",
                "decade_exponent": 4,
                "n": 20000,
                "p_n": 224737,
            }
        ]
        result_rows = build_off_lattice_result_rows(dataset_rows)
        self.assertEqual(len(result_rows), len(COMPARATOR_SPECS))
        self.assertEqual({row["comparator"] for row in result_rows}, {spec["name"] for spec in COMPARATOR_SPECS})

    def test_summary_includes_stage_decision(self) -> None:
        rows = []
        stage_exponents = {"stage_a": 13, "stage_b": 15, "stage_c": 17}
        families = ["off_lattice_decimal", "boundary_window", "dense_local_window"]
        for stage_name, exponent in stage_exponents.items():
            for family in families:
                for comparator_index, spec in enumerate(COMPARATOR_SPECS):
                    comparator = spec["name"]
                    seed_ppm = 10.0 + comparator_index
                    if comparator == "lpp_seed":
                        seed_ppm = 1.0
                    rows.append(
                        {
                            "row_id": f"{family}__{stage_name}__{comparator}",
                            "stage": stage_name,
                            "family": family,
                            "decade_exponent": exponent,
                            "n": 10**exponent,
                            "p_n": 10**exponent + 7,
                            "comparator": comparator,
                            "seed": 0,
                            "seed_signed_error": 1 if comparator == "lpp_seed" else 10 + comparator_index,
                            "seed_absolute_error": 1 if comparator == "lpp_seed" else 10 + comparator_index,
                            "seed_rel_ppm": seed_ppm,
                            "refined_predictor": 0,
                            "refined_signed_error": 0,
                            "refined_absolute_error": 0,
                            "refined_rel_ppm": 0.0,
                        }
                    )
        summary = summarize_off_lattice_results(rows)
        self.assertEqual(summary["decision"]["conclusion"], "survives strongly")
        self.assertEqual(summary["decision"]["total_stage_family_cells"], 9)

    def test_write_off_lattice_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_root = Path(tmp_dir_name)
            (tmp_root / "data").mkdir()
            (tmp_root / "benchmarks").mkdir()
            dataset_rows = [
                {
                    "row_id": "off_lattice_decimal__k4__m2",
                    "family": "off_lattice_decimal",
                    "decade_exponent": 4,
                    "n": 20000,
                    "p_n": 224737,
                },
                {
                    "row_id": "boundary_window__k4__offset+0",
                    "family": "boundary_window",
                    "decade_exponent": 4,
                    "n": 10000,
                    "p_n": 104729,
                },
            ]
            from lpp import off_lattice_benchmark as bench

            write_held_out_dataset(tmp_root / "data" / bench.HELD_OUT_DATASET, dataset_rows)
            artifacts = write_off_lattice_benchmark_artifacts(tmp_root, stage_names=["baseline"])
            self.assertTrue(artifacts["csv"].exists())
            self.assertTrue(artifacts["summary"].exists())
            self.assertTrue(artifacts["markdown"].exists())
            summary = json.loads(artifacts["summary"].read_text())
            self.assertIn("overall", summary)
