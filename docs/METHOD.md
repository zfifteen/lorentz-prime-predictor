# Method

This document defines the shipped runtime contract for `lpp_seed` and `lpp_refined_predictor`.

It is separate from the benchmark-leader summary in [CANDIDATE_CATEGORIES.md](./CANDIDATE_CATEGORIES.md).

The Lorentz Prime Predictor defines two related objects, and this repository keeps them separate in both prose and measurement.

## Official Seed

$$ lpp\_seed(n) = r\_inverse\_seed(n) $$

`lpp_seed` is now the repository's official deterministic inversion seed. It returns an integer estimate for the $n$th prime for $n \geq 1$.

For the main regime, this is the fixed-step inverse construction defined in [FORMULA.md](./FORMULA.md). For the narrow low-index compatibility window below `100`, the runtime uses the legacy closed-form path so the public API stays defined on the full declared domain.

This is the correct object for the repo's primary seed contract. The older closed-form path and the other comparison formulas remain available as alternates, not as the shipped default.

## Refined Predictor

$$ lpp\_refined\_predictor(n) = nextPrime(lpp\_seed(n) - 1) $$

`lpp_refined_predictor` starts at the official seed and moves forward deterministically until a prime output is reached, again for $n \geq 1$.

This answers a different question. It measures whether the shipped seed is a useful launch point for a practical prime-returning method, not only whether the seed lands near $p_n$.

## Why the Separation Matters

A strong refined predictor does not by itself prove a stronger seed formula. A strong seed formula does not by itself prove the best prime-output stack. The two layers support different claims and must not be merged into one headline result.

For this repository, that means:

- seed tables report seed accuracy only
- refined tables report prime-output accuracy only
- summary language must name which estimand is being discussed
- refined comparisons are valid only when the refinement rule is shared across predictors

## Alternate Seeds

The codebase also exposes:

- `legacy_lpp_seed`
- `cipolla_log5_repacked_seed`
- `li_inverse_seed`
- `r_inverse_seed`

`r_inverse_seed` is the explicit method name for the same construction that now ships as `lpp_seed`. The other three names are alternate formulas retained for benchmark and research work.
