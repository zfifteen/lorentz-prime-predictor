from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "KNOWN_PRIMES.md"
MANIFEST_PATH = REPO_ROOT / "data" / "KNOWN_PRIMES_MANIFEST.json"
DEFAULT_MIN_EXPONENT = 19
DEFAULT_MAX_EXPONENT = 24


def _require_primecount() -> str:
    result = subprocess.run(
        ["primecount", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("primecount is required to generate the exact contract grid")
    return result.stdout.strip()


def _nth_prime(exponent: int) -> tuple[str, float, str]:
    n_value = f"1e{exponent}"
    command = ["primecount", n_value, "--nth-prime", "--threads=1"]
    started = time.perf_counter()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise SystemExit(
            f"primecount failed for 10^{exponent}: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip(), elapsed, " ".join(command)


def main(argv: list[str]) -> int:
    min_exponent = DEFAULT_MIN_EXPONENT
    max_exponent = DEFAULT_MAX_EXPONENT
    if len(argv) == 3:
        min_exponent = int(argv[1])
        max_exponent = int(argv[2])
    elif len(argv) != 1:
        raise SystemExit("usage: generate_known_primes_primecount.py [MIN_EXPONENT MAX_EXPONENT]")

    if min_exponent > max_exponent:
        raise SystemExit("MIN_EXPONENT must be <= MAX_EXPONENT")

    version = _require_primecount()
    rows: list[dict[str, object]] = []
    for exponent in range(min_exponent, max_exponent + 1):
        prime_value, elapsed, command = _nth_prime(exponent)
        rows.append(
            {
                "exponent": exponent,
                "n": f"1e{exponent}",
                "prime": prime_value,
                "command": command,
                "elapsed_seconds": elapsed,
            }
        )

    payload = {
        "oracle": "primecount",
        "oracle_version": version,
        "host": platform.platform(),
        "python": sys.version.split()[0],
        "target_dataset": str(DATA_PATH),
        "rows": rows,
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(MANIFEST_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
