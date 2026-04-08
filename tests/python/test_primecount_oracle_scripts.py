from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEADING_MESSAGE = "primecount is banned from the active local workflow in this repository."
SCRIPT_PATHS = [
    ROOT / "scripts" / "generate_known_primes_primecount.py",
    ROOT / "scripts" / "verify_known_primes_primecount.py",
    ROOT / "scripts" / "generate_held_out_exact_primes.py",
    ROOT / "scripts" / "verify_held_out_exact_primes.py",
]


class PrimecountOracleScriptTests(unittest.TestCase):
    def test_banned_oracle_scripts_fail_fast(self) -> None:
        for script_path in SCRIPT_PATHS:
            with self.subTest(script=script_path.name):
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(LEADING_MESSAGE, f"{result.stdout}\n{result.stderr}")


if __name__ == "__main__":
    unittest.main()
