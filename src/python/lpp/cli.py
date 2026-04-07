from __future__ import annotations

import sys

from .predictor import lpp_refined_predictor, lpp_seed
from .version import VERSION


def _parse_n(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("N must be an integer") from exc


def main() -> int:
    args = sys.argv[1:]

    if not args:
        print("usage: lpp {seed|refine|version} [N]", file=sys.stderr)
        return 1

    command = args[0]

    try:
        if command == "version":
            if len(args) != 1:
                raise ValueError("version takes no arguments")
            print(VERSION)
            return 0

        if command == "seed":
            if len(args) != 2:
                raise ValueError("seed requires exactly one integer argument")
            print(lpp_seed(_parse_n(args[1])))
            return 0

        if command == "refine":
            if len(args) != 2:
                raise ValueError("refine requires exactly one integer argument")
            print(lpp_refined_predictor(_parse_n(args[1])))
            return 0

        raise ValueError(f"unknown command: {command}")
    except (TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
