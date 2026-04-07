from __future__ import annotations

import sys


MESSAGE = (
    "primecount is banned from the active local workflow in this repository.\n"
    "The shipped contract grid is consumed as a committed exact artifact.\n"
    "Local verification in this repo should not invoke primecount."
)


def main(argv: list[str]) -> int:
    raise SystemExit(MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
