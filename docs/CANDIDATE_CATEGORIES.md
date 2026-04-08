# Candidate Categories

This repository is now tracking different categories of nth-prime candidates against the same benchmark datasets.

That split matters because not every strong candidate is the same kind of mathematical object.

## Closed-Form Seed Category

A closed-form seed is a straight-line algebraic formula for an integer estimate of $p_n$.

Current best candidate in this category:

- `cipolla_log5_repacked`

Current exact reading:

- it beats `li_inverse_seed` on exact `stage_a` and exact `stage_b`
- it leads through exact `10^16`
- it loses at exact `10^17` and exact `10^18`

Primary artifact:

- [benchmarks/cipolla_repacked_probe/README.md](../benchmarks/cipolla_repacked_probe/README.md)

## Deterministic Inversion Seed Category

A deterministic inversion seed solves a fixed analytic counting equation by a fixed deterministic rule.

Current best candidate in this category:

- `r_inverse_seed`

Construction:

- truncate the Riemann prime-counting function at `K = 8`
- start from `cipolla_log5_repacked`
- apply exactly `2` Newton steps

Current exact reading:

- it beats `li_inverse_seed` on exact anchors from `10^12` through `10^18`
- it beats `li_inverse_seed` across every exact family in `stage_a` and `stage_b`
- it does not beat `li_inverse_seed` on the current local continuation stage

Primary artifact:

- [benchmarks/r_inverse_probe/README.md](../benchmarks/r_inverse_probe/README.md)

## Refined Prime-Output Category

This is the category for deterministic prime-returning methods, not only seed formulas.

Current repository object in this category:

- `lpp_refined_predictor`

It answers a different question from the seed categories above. It measures prime-output utility, not only seed closeness.

## Why the Split Matters

These categories should be judged on the same benchmark datasets, but they should not be merged into one claim.

- a stronger inversion seed does not automatically replace the best closed-form seed
- a stronger closed-form seed does not automatically replace the best prime-output method
- each category should keep its own leader and its own claim language
