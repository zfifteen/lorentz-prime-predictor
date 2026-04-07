# Method

The Lorentz Prime Predictor defines two related objects, and this repository keeps them separate in both prose and measurement.

## Closed-Form Seed

$$ lpp_seed(n) = \widehat{p}_n $$

`lpp_seed` is the analytic object defined in [FORMULA.md](./FORMULA.md). It returns an integer estimate for the $n$th prime for $n \geq 5$.

This is the correct object for direct comparison against other closed-form nth-prime formulas. When the question is formula accuracy, the seed is the estimand.

## Refined Predictor

$$ lpp_refined_predictor(n) = nextPrime(\widehat{p}_n - 1) $$

`lpp_refined_predictor` starts at the seed and moves forward deterministically until a prime output is reached, again for $n \geq 5$.

This answers a different question. It measures whether the seed is a useful launch point for a practical prime-returning method, not only whether the closed-form expression lands near $p_n$.

## Why the Separation Matters

A strong refined predictor does not by itself prove a stronger closed-form formula. A strong closed-form formula does not by itself prove the best prime-output stack. The two layers support different claims and must not be merged into one headline result.

For this repository, that means:

- seed tables report closed-form accuracy only
- refined tables report prime-output accuracy only
- summary language must name which estimand is being discussed
- refined comparisons are valid only when the refinement rule is shared across predictors

## Output Contract

The first implementation in this repository should make the contract explicit:

- `lpp_seed` returns an integer estimate
- `lpp_refined_predictor` returns a prime output
- benchmark reports state clearly which object is being measured
- both value error and rank error are reported where applicable

That separation is part of the scientific contract of the repository, not a presentation preference.
