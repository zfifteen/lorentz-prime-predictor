from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


import scripts.generate_known_primes_primecount as generate_script
import scripts.verify_known_primes_primecount as verify_script


class PrimecountOracleScriptTests(unittest.TestCase):
    def test_generate_script_requires_primecount(self) -> None:
        with patch.object(generate_script.subprocess, "run") as run_mock:
            run_mock.return_value.returncode = 1
            run_mock.return_value.stdout = ""
            run_mock.return_value.stderr = ""
            with self.assertRaises(SystemExit) as exc:
                generate_script.main(["generate_known_primes_primecount.py"])
            self.assertIn("primecount is required", str(exc.exception))

    def test_generate_script_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            manifest_path = Path(tmp_dir_name) / "KNOWN_PRIMES_MANIFEST.json"
            with patch.object(generate_script, "MANIFEST_PATH", manifest_path):
                with patch.object(generate_script, "_require_primecount", return_value="primecount 8.4"):
                    with patch.object(
                        generate_script,
                        "_nth_prime",
                        side_effect=[
                            ("465675465116607065549", 0.25, "primecount 1e19 --nth-prime --threads=1"),
                            ("4892055594575155744537", 0.5, "primecount 1e20 --nth-prime --threads=1"),
                        ],
                    ):
                        result = generate_script.main(
                            ["generate_known_primes_primecount.py", "19", "20"]
                        )
            self.assertEqual(result, 0)
            payload = json.loads(manifest_path.read_text())
            self.assertEqual(payload["oracle"], "primecount")
            self.assertEqual(len(payload["rows"]), 2)
            self.assertEqual(payload["rows"][0]["exponent"], 19)

    def test_verify_script_requires_primecount(self) -> None:
        with patch.object(verify_script.subprocess, "run") as run_mock:
            run_mock.return_value.returncode = 1
            run_mock.return_value.stdout = ""
            run_mock.return_value.stderr = ""
            with self.assertRaises(SystemExit) as exc:
                verify_script.main(["verify_known_primes_primecount.py"])
            self.assertIn("primecount is required", str(exc.exception))

    def test_verify_script_single_band(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            data_path = Path(tmp_dir_name) / "KNOWN_PRIMES.md"
            data_path.write_text(
                "# Known Primes (Ground Truth)\n\n"
                "| Index (n) | n (Scientific) | Prime (p_n) | Source |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| 10000000000000000000 | 10^19 | 465675465116607065549 | OEIS A006988 |\n"
                "| 1000000000000000000000000 | 10^24 | 58310039994836584070534263 | OEIS A006988 |\n"
            )
            with patch.object(verify_script, "DATA_PATH", data_path):
                with patch.object(verify_script, "_require_primecount", return_value=None):
                    with patch.object(verify_script, "_verify_one", return_value=None) as verify_one_mock:
                        result = verify_script.main(["verify_known_primes_primecount.py", "24"])
            self.assertEqual(result, 0)
            verify_one_mock.assert_called_once_with(
                1000000000000000000000000,
                58310039994836584070534263,
            )
