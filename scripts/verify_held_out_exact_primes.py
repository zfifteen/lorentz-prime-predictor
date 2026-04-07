from __future__ import annotations

import sys


MESSAGE = (
    "primecount is banned from the active local workflow in this repository.\n"
    "Held-out exact datasets remain committed historical artifacts with recorded provenance.\n"
    "Local runs should consume the checked-in datasets directly and use the Z5D C predictor for prediction work."
)


def main(argv: list[str]) -> int:
    raise SystemExit(MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
