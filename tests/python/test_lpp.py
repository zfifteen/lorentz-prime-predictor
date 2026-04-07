from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from sympy import isprime

from lpp import get_version, lpp_refined_predictor, lpp_seed


ROOT = Path(__file__).resolve().parents[2]


class LPPTests(unittest.TestCase):
    def test_get_version(self) -> None:
        self.assertEqual(get_version(), "0.1.0")

    def test_seed_known_values(self) -> None:
        self.assertEqual(lpp_seed(1), 2)
        self.assertEqual(lpp_seed(2), 3)
        self.assertEqual(lpp_seed(3), 4)
        self.assertEqual(lpp_seed(4), 5)
        self.assertEqual(lpp_seed(10), 17)
        self.assertEqual(lpp_seed(100), 508)
        self.assertEqual(lpp_seed(1000), 7857)

    def test_seed_matches_reference_precision_at_canonical_points(self) -> None:
        expected = {
            10: 17,
            100: 508,
            1000: 7857,
            10000: 104690,
            100000: 1300252,
            1000000: 15490400,
            10000000: 179481332,
            100000000: 2038426563,
            1000000000: 22804083540,
        }
        for n, value in expected.items():
            with self.subTest(n=n):
                self.assertEqual(lpp_seed(n), value)

    def test_refined_output_is_prime(self) -> None:
        value = lpp_refined_predictor(1000)
        self.assertTrue(isprime(value))
        self.assertGreaterEqual(value, lpp_seed(1000))
        self.assertEqual(value, 7919)

    def test_refined_matches_legacy_grid(self) -> None:
        expected = {
            1: 2,
            10: 29,
            100: 541,
            1000: 7919,
            10000: 104729,
            100000: 1299709,
            1000000: 15485863,
        }
        for n, value in expected.items():
            with self.subTest(n=n):
                self.assertEqual(lpp_refined_predictor(n), value)

    def test_input_validation(self) -> None:
        with self.assertRaises(TypeError):
            lpp_seed(10.0)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            lpp_seed(0)

    def test_cli_version(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "lpp", "version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env={"PYTHONPATH": str(ROOT / "src/python")},
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "0.1.0\n")

    def test_cli_seed(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "lpp", "seed", "1000"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env={"PYTHONPATH": str(ROOT / "src/python")},
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "7857\n")

    def test_cli_refine(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "lpp", "refine", "1000"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env={"PYTHONPATH": str(ROOT / "src/python")},
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "7919\n")


if __name__ == "__main__":
    unittest.main()
