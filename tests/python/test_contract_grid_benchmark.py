from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lpp.contract_grid_benchmark import build_contract_grid_rows, write_contract_grid_artifacts


ROOT = Path(__file__).resolve().parents[2]
KNOWN_BANDS = 25


class ContractGridBenchmarkTests(unittest.TestCase):
    def test_contract_grid_matches_exact_ground_truth(self) -> None:
        rows = build_contract_grid_rows(ROOT / "data" / "KNOWN_PRIMES.md")
        self.assertEqual(len(rows), KNOWN_BANDS)
        self.assertTrue(all(bool(row["exact_match"]) for row in rows))
        self.assertEqual(rows[0]["band"], "10^0")
        self.assertEqual(rows[-1]["band"], "10^24")
        self.assertEqual(rows[-1]["lpp_refined_predictor"], rows[-1]["p_n"])

    def test_contract_grid_writes_all_band_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            artifacts = write_contract_grid_artifacts(ROOT, output_dir=tmp_dir)
            summary = json.loads(artifacts["summary"].read_text())
            self.assertEqual(len(summary), KNOWN_BANDS)
            self.assertTrue(all(entry["lpp"]["exact_match"] for entry in summary))
            self.assertTrue((tmp_dir / "band_10_0.json").exists())
            self.assertTrue((tmp_dir / "band_10_24.json").exists())
            self.assertIn("Exact contract result", artifacts["markdown"].read_text())
