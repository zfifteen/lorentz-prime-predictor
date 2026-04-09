#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from lpp.r_inverse_sensitivity import write_sensitivity_artifacts


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    artifacts = write_sensitivity_artifacts(REPO_ROOT)
    print(f"Wrote rowwise results to {artifacts['rowwise']}")
    print(f"Wrote family summary to {artifacts['family_summary']}")
    print(f"Wrote anchor summary to {artifacts['anchor_summary']}")
    print(f"Wrote README to {artifacts['readme']}")


if __name__ == "__main__":
    main()
