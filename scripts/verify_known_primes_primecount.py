from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "KNOWN_PRIMES.md"


def _require_primecount() -> None:
    result = subprocess.run(
        ["primecount", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("primecount is required to verify the exact contract grid")


def _parse_rows() -> list[tuple[int, int]]:
    rows: list[tuple[int, int]] = []
    for line in DATA_PATH.read_text().splitlines():
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 3:
            continue
        try:
            n_value = int(parts[0].replace(",", "").replace("_", ""))
            p_value = int(parts[2].replace(",", "").replace("_", ""))
        except ValueError:
            continue
        rows.append((n_value, p_value))
    return rows


def _verify_one(n_value: int, p_value: int) -> None:
    result = subprocess.run(
        ["primecount", str(n_value), "--nth-prime", "--threads=1"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"primecount failed for n={n_value}: {result.stderr.strip() or result.stdout.strip()}"
        )
    observed = int(result.stdout.strip())
    if observed != p_value:
        raise SystemExit(f"mismatch for n={n_value}: got {observed}, expected {p_value}")


def main(argv: list[str]) -> int:
    _require_primecount()
    rows = _parse_rows()
    if len(argv) == 2:
        target_exponent = int(argv[1])
        rows = [(n_value, p_value) for n_value, p_value in rows if n_value == 10**target_exponent]
        if not rows:
            raise SystemExit(f"no shipped row for exponent {target_exponent}")
    elif len(argv) != 1:
        raise SystemExit("usage: verify_known_primes_primecount.py [EXPONENT]")

    for n_value, p_value in rows:
        _verify_one(n_value, p_value)

    print("verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
