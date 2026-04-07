from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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


ROOT = Path(__file__).resolve().parents[2]


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


class OracleScriptTests(unittest.TestCase):
    def test_generate_script_requires_primecount(self) -> None:
        import scripts.generate_held_out_exact_primes as script

        with patch.object(script.subprocess, "run") as run_mock:
            run_mock.return_value.returncode = 1
            run_mock.return_value.stdout = ""
            run_mock.return_value.stderr = ""
            with self.assertRaises(SystemExit) as exc:
                script.main(["generate_held_out_exact_primes.py"])
            self.assertIn("primecount is required", str(exc.exception))

    def test_verify_script_requires_primecount(self) -> None:
        import scripts.verify_held_out_exact_primes as script

        with patch.object(script.subprocess, "run") as run_mock:
            run_mock.return_value.returncode = 1
            run_mock.return_value.stdout = ""
            run_mock.return_value.stderr = ""
            with self.assertRaises(SystemExit) as exc:
                script.main(["verify_held_out_exact_primes.py"])
            self.assertIn("primecount is required", str(exc.exception))

    def test_verify_script_family_and_decade_filters(self) -> None:
        import scripts.verify_held_out_exact_primes as script
        from lpp import off_lattice_benchmark as bench

        rows = [
            {
                "row_id": "off_lattice_decimal__k4__m2",
                "family": "off_lattice_decimal",
                "decade_exponent": 4,
                "n": 20000,
                "p_n": 224737,
            },
            {
                "row_id": "boundary_window__k5__offset+0",
                "family": "boundary_window",
                "decade_exponent": 5,
                "n": 100000,
                "p_n": 1299709,
            },
            {
                "row_id": "boundary_window__k5__offset+1",
                "family": "boundary_window",
                "decade_exponent": 5,
                "n": 100001,
                "p_n": 1299721,
            },
        ]
        call_outputs = [
            type("R", (), {"returncode": 0, "stdout": "primecount 8.4\n", "stderr": ""})(),
            type("R", (), {"returncode": 0, "stdout": "1299709\n", "stderr": ""})(),
        ]
        with patch.object(bench, "parse_held_out_dataset", return_value=rows):
            with patch.object(script.subprocess, "run", side_effect=call_outputs) as run_mock:
                result = script.main(
                    ["verify_held_out_exact_primes.py", "--family", "boundary_window", "--decade", "5"]
                )
        self.assertEqual(result, 0)
        self.assertEqual(run_mock.call_count, 2)

    def test_generate_script_writes_manifest(self) -> None:
        import scripts.generate_held_out_exact_primes as script
        from lpp import off_lattice_benchmark as bench

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_root = Path(tmp_dir_name)
            (tmp_root / "data").mkdir()
            rows = [
                {
                    "row_id": "off_lattice_decimal__k4__m2",
                    "family": "off_lattice_decimal",
                    "decade_exponent": 4,
                    "n": 20000,
                },
                {
                    "row_id": "off_lattice_decimal__k4__m2_dup",
                    "family": "dense_local_window",
                    "decade_exponent": 4,
                    "n": 20000,
                },
                {
                    "row_id": "off_lattice_decimal__k4__m2_next",
                    "family": "dense_local_window",
                    "decade_exponent": 4,
                    "n": 20001,
                },
            ]
            version_result = type("R", (), {"returncode": 0, "stdout": "primecount 8.4\n", "stderr": ""})()
            nth_result = type("R", (), {"returncode": 0, "stdout": "224737\n", "stderr": ""})()
            with patch.object(script, "REPO_ROOT", tmp_root):
                with patch.object(script, "PYTHON_SRC", ROOT / "src" / "python"):
                    with patch.object(bench, "build_stage_specs", return_value=rows):
                        with patch.object(bench, "get_stage_spec", return_value={"dataset": "x.csv", "manifest": "x_manifest.json"}):
                            with patch.object(script.platform, "platform", return_value="test-host"):
                                with patch.object(script.subprocess, "run", side_effect=[version_result, nth_result]):
                                    with patch.object(script.gp, "next_prime", return_value=224743):
                                        result = script.main(["generate_held_out_exact_primes.py"])
            self.assertEqual(result, 0)
            manifest_path = tmp_root / "data" / "x_manifest.json"
            dataset_path = tmp_root / "data" / "x.csv"
            self.assertTrue(dataset_path.exists())
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["row_count"], 3)
            self.assertEqual(manifest["run_count"], 1)
