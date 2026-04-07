# Problem Statement: Derive a Stronger $k^*(n)$ Without Heuristics

## Goal

Find a stronger formula for the lift coefficient $k^*(n)$ in the LPP seed, but only if the formula is honestly derived.

The standard is strict:

- stronger empirical performance is not enough
- no fitted decimal constants
- no chosen coefficients justified only by good benchmark behavior
- no sign flips or denominator changes unless they are themselves derived
- every coefficient must come from the derivation

If a candidate is empirically strong but any part of it is chosen rather than forced, it is rejected.

## Seed Structure

The seed has the form

$$
\widehat{p}_n = \left\lfloor P(n) + d(n) + e(n) + \frac{1}{2} \right\rfloor
$$

with backbone

$$
P(n) = n\left(\ln n + \ln\ln n - 1 + \frac{\ln\ln n - 2}{\ln n}\right)
$$

and backbone density

$$
B(n) = \frac{P(n)}{n}
$$

The downward bend is

$$
d(n) = c(n)P(n)\left(\frac{\ln P(n)}{e^4}\right)^2
$$

with

$$
c(n) = -\frac{e^8\left((\ln\ln P(n))^2 - 6\ln\ln P(n) + 11\right)}{2(\ln P(n))^5}
$$

The lift is

$$
e(n) = k^*(n)P(n)^{2/3}
$$

The open problem is to derive $k^*(n)$.

## Current Accepted Derived Baseline

The currently acceptable non-heuristic lift is the strict first-order truncation of the original singular lift's geometric expansion:

$$
k^*(n) = \frac{2B(n) + e^2}{4e^2B(n)} = \frac{1}{2e^2} + \frac{1}{4B(n)}
$$

This is acceptable because the coefficient of the first correction term is forced by the expansion of the original expression.

## Original Rejected Lift

The earlier lift was

$$
k_{\mathrm{old}}(n) = \frac{1}{e^2\left(2 - \frac{e^2}{B(n)}\right)}
$$

This has a pole when

$$
B(n) = \frac{e^2}{2}
$$

which occurs between $n=36$ and $n=37$ for this backbone.

That lift is rejected because the pole is a fatal structural flaw.

## Important Distinction

The problem is not:

"find the best-looking $k^*(n)$."

The problem is:

"find the strongest $k^*(n)$ whose coefficients and shape are derivationally forced."

That distinction matters.

Several stronger candidates were already rejected because they were heuristic.

## Rejected Heuristic Pattern

A previously stronger empirical candidate had the form

$$
k^*(n) = \frac{B(n) + e^2}{2e^2B(n)} = \frac{1}{2e^2} + \frac{1}{2B(n)}
$$

It performed well, but it is rejected because the $1/B(n)$ coefficient is doubled relative to the true first-order expansion. That coefficient was not derived. It was effectively chosen for behavior.

So under the current standard, that candidate is not acceptable.

## Empirical Context

Against `li_inverse_seed`, the current strict-derived lift has this exact pattern:

- it is much better in the low published regime
- `li_inverse_seed` takes over around $10^7$
- `li_inverse_seed` remains dramatically better on the deeper exact stages

Current exact comparison numbers:

- published exact grid max ppm:
  - strict-derived $k^*$: `553.810310`
  - `li_inverse_seed`: `4382.740215`
- reproducible exact baseline max ppm:
  - strict-derived $k^*$: `1433.202197`
  - `li_inverse_seed`: `5271.714558`
- reproducible exact `stage_a` max ppm:
  - strict-derived $k^*$: `11.286788`
  - `li_inverse_seed`: `0.089328`
- reproducible exact `stage_b` max ppm:
  - strict-derived $k^*$: `5.892607`
  - `li_inverse_seed`: `0.010553`

So the current derived lift is honest, but not yet strong enough.

## What Counts as an Acceptable Solution

An acceptable new $k^*(n)$ must satisfy all of these:

1. It is derived from the existing structure, not tuned from benchmarks.
2. Every coefficient is forced by algebra, asymptotics, or another stated structural law.
3. It is closed form.
4. It has no pole or sign flip on the valid integer domain of the full seed.
5. It preserves or improves on the current derived baseline empirically.
6. The derivation is short enough to audit line by line.

## What Does Not Count

These do not count as acceptable:

- choosing a coefficient because it improves ppm
- choosing a sign because it stabilizes the low regime
- inserting a shift like $B(n) + c$ unless $c$ is derived
- using a Pade or rational form with free coefficients fitted numerically
- claiming a formula is "derived" because it is simple

Simplicity matters, but simplicity alone is not derivation.

## Acceptable Search Space

These directions are acceptable:

1. Higher-order truncations of the geometric expansion of $k_{\mathrm{old}}(n)$.
2. Rational approximants whose coefficients are fixed by matching the series of $k_{\mathrm{old}}(n)$, not by fitting.
3. A derivation from another project law, such as divisor-density structure, only if that law forces the coefficients.
4. An inversion argument that solves the residual lift term after the asymptotic $c(n)$ bend, provided the solution introduces no chosen constants.

## Preferred Output

Produce:

1. A candidate formula for $k^*(n)$.
2. A derivation that shows where every coefficient comes from.
3. A proof or clear argument that the formula has no pole on the valid domain.
4. A brief explanation of why it is not heuristic.
5. A benchmark comparison against:
   - the current strict-derived baseline
   - `li_inverse_seed`
6. A short statement of whether the candidate should replace the current baseline.

## If No Stronger Derived Formula Exists

Say that plainly.

Do not smuggle in a chosen coefficient and call it derived.

## Repository Context

Relevant artifacts inside this repository:

- [ASYMP_C_BACKBONE_RATIO_K.md](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/docs/ASYMP_C_BACKBONE_RATIO_K.md)
- [probe_k_derivation.py](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/scripts/probe_k_derivation.py)
- [k_probe_summary.csv](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/benchmarks/k_derivation_probe/k_probe_summary.csv)
- [claude_vs_li_inverse_summary.csv](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/benchmarks/k_derivation_probe/claude_vs_li_inverse_summary.csv)
- [published_exact_point_comparison.csv](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/benchmarks/k_derivation_probe/published_exact_point_comparison.csv)

## One-Sentence Version

Derive a closed-form $k^*(n)$ that is stronger than the current strict-derived baseline, but reject any candidate whose coefficients are chosen rather than mathematically forced.
