from __future__ import annotations

import subprocess
import sys
import unittest
import warnings
from pathlib import Path

from sympy import isprime

from lpp import (
    cipolla_log5_repacked_seed,
    get_version,
    legacy_lpp_seed,
    li_inverse_seed,
    lpp_refined_predictor,
    lpp_seed,
    r_inverse_seed,
)


ROOT = Path(__file__).resolve().parents[2]


class LPPTests(unittest.TestCase):
    def test_get_version(self) -> None:
        self.assertEqual(get_version(), "0.1.0")

    def test_official_seed_is_r_inverse(self) -> None:
        for n in (1, 10, 100, 1000, 10**12, 10**17, 10**18):
            with self.subTest(n=n):
                self.assertEqual(lpp_seed(n), r_inverse_seed(n))

    def test_official_seed_known_values(self) -> None:
        expected = {
            1: 2,
            2: 3,
            3: 4,
            4: 5,
            10: 17,
            100: 537,
            1000: 7923,
            10000: 104768,
            10**12: 29996225393473,
            10**17: 4185296581676470097,
            10**18: 44211790234127235508,
        }
        for n, value in expected.items():
            with self.subTest(n=n):
                self.assertEqual(lpp_seed(n), value)

    def test_alternate_seeds_known_values(self) -> None:
        self.assertEqual(legacy_lpp_seed(1000), 7857)
        self.assertEqual(cipolla_log5_repacked_seed(1000), 7761)
        self.assertEqual(li_inverse_seed(1000), 7763)

    def test_seed_emits_no_local_context_deprecation_warning(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            value = lpp_seed(1000)
        self.assertEqual(value, 7923)
        messages = [str(warning.message) for warning in caught if issubclass(warning.category, DeprecationWarning)]
        self.assertNotIn("local_context() is deprecated, use context(get_context()) instead.", messages)

    def test_refined_output_is_prime(self) -> None:
        value = lpp_refined_predictor(1000)
        self.assertTrue(isprime(value))
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
            10000000000000000000: 465675465116607065549,
            100000000000000000000: 4892055594575155744537,
            1000000000000000000000: 51271091498016403471853,
            10000000000000000000000: 536193870744162118627429,
            100000000000000000000000: 5596564467986980643073683,
            1000000000000000000000000: 58310039994836584070534263,
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
        self.assertEqual(result.stdout, "7923\n")

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
