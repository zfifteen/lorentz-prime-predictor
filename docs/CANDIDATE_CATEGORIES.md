# Candidate Categories

This repository keeps one retained leader in each candidate category and judges them on the same official benchmark suite.

That split matters because not every strong result is the same kind of mathematical object.

## Closed-Form Seed Category

A closed-form seed is a straight-line algebraic formula for an integer estimate of $p_n$.

Current decision:

- `cipolla_log5_repacked`

Current exact reading:

- on the official exact anchor suite, it stays ahead of `li_inverse_seed` through `10^16`
- it leads through exact `10^16`
- it loses at exact `10^17` and exact `10^18`
- supporting exact stage-based probes also keep it ahead of `li_inverse_seed` through the committed exact `stage_b` horizon

Official suite artifact:

- [benchmarks/power_of_ten_anchor_suite/README.md](../benchmarks/power_of_ten_anchor_suite/README.md)

Supporting artifact:

- [benchmarks/cipolla_repacked_probe/README.md](../benchmarks/cipolla_repacked_probe/README.md)

## Deterministic Inversion Seed Category

A deterministic inversion seed solves a fixed analytic counting equation by a fixed deterministic rule.

Current decision:

- `r_inverse_seed`

Official runtime identity:

- `lpp_seed` now uses this construction as the shipped default path

Construction:

- truncate the Riemann prime-counting function at `K = 8`
- start from `cipolla_log5_repacked`
- apply exactly `2` Newton steps

Current exact reading:

- on the official exact anchor suite, it is sole best on `16` anchors, tied best at `10^4`, and best-or-tied-best on every anchor where it is defined from `10^2` through `10^18`
- supporting exact stage-based probes also keep it ahead of `li_inverse_seed` across every committed exact family in `stage_a` and `stage_b`
- it does not beat `li_inverse_seed` on the current local continuation stage

Official suite artifact:

- [benchmarks/power_of_ten_anchor_suite/README.md](../benchmarks/power_of_ten_anchor_suite/README.md)

Supporting artifact:

- [benchmarks/r_inverse_probe/README.md](../benchmarks/r_inverse_probe/README.md)

## Refined Prime-Output Category

This is the category for deterministic prime-returning methods, not only seed formulas.

Current repository object in this category:

- `lpp_refined_predictor`

It answers a different question from the seed categories above. It measures prime-output utility, not only seed closeness.

## Why the Split Matters

These categories are judged on the same official benchmark suite, but they should not be merged into one claim.

- a stronger inversion seed does not automatically replace the best closed-form seed
- a stronger closed-form seed does not automatically replace the best prime-output method
- each category should keep its own leader and its own claim language

This document records the current decisions only. The longer search history belongs in benchmark artifacts, not here.
