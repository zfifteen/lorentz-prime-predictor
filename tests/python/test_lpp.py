from __future__ import annotations

import subprocess
import sys
import unittest
import warnings
from pathlib import Path
from importlib import util

from sympy import isprime

from lpp import get_version, lpp_refined_predictor, lpp_seed


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_REPO = Path("/Users/velocityworks/IdeaProjects/archive/z5d-prime-predictor")
REFERENCE_PREDICTOR = REFERENCE_REPO / "src/python/z5d_predictor/predictor.py"


def _load_reference_module():
    spec = util.spec_from_file_location("z5d_reference_predictor", REFERENCE_PREDICTOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load reference predictor from {REFERENCE_PREDICTOR}")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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

    def test_seed_emits_no_local_context_deprecation_warning(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            value = lpp_seed(1000)
        self.assertEqual(value, 7857)
        messages = [str(warning.message) for warning in caught if issubclass(warning.category, DeprecationWarning)]
        self.assertNotIn("local_context() is deprecated, use context(get_context()) instead.", messages)

    def test_seed_matches_reference_closed_form_on_legacy_regime(self) -> None:
        reference = _load_reference_module()
        for exponent in range(1, 18):
            n = 10**exponent
            with self.subTest(n=n):
                self.assertEqual(lpp_seed(n), int(reference.closed_form_estimate(n)))

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
