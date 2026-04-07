from __future__ import annotations

import sys


MESSAGE = (
    "primecount is banned from the active local workflow in this repository.\n"
    "Held-out exact datasets are committed artifacts, not something this repo regenerates locally.\n"
    "Use the checked-in data files for exact benchmark labels and use the Z5D C predictor for local prediction work."
)


def main(argv: list[str]) -> int:
    raise SystemExit(MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
