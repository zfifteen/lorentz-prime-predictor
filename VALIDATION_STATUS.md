# Validation Status

This document records what has and has not been validated in the repository at the current stage.

## Current State

The repository is still in the pre-implementation research-contract phase.

What is currently complete:

- the public vocabulary
- the origin narrative
- the closed-form seed definition
- the seed domain and rounding contract
- the seed-versus-refined method distinction
- the benchmark protocol
- the public claim boundary
- the reference set for future implementation and benchmarking
- the intended public API contract

What is not yet complete:

- reference implementation code
- direct unit tests
- comparator implementations
- exact-oracle selection for benchmark runs
- benchmark artifacts
- sensitivity tables
- timing harness

## Status Table

| Area | Status | Notes |
|---|---|---|
| Conceptual framing | complete | [ORIGIN.md](./ORIGIN.md) and [README.md](./README.md) are aligned. |
| Formula specification | complete | [FORMULA.md](./FORMULA.md) fixes the current seed, constants, domain, and rounding rule. |
| Method specification | complete | [METHOD.md](./METHOD.md) fixes the seed/refined separation. |
| Benchmark contract | complete | [BENCHMARK_PROTOCOL.md](./BENCHMARK_PROTOCOL.md) defines the evaluation rules. |
| Public claim boundary | complete | [CLAIMS.md](./CLAIMS.md) defines what the repo may and may not say. |
| Reference set | complete | [REFERENCES.md](./REFERENCES.md) records the baseline citation targets. |
| Public API contract | complete | [API.md](./API.md) defines the intended minimal Python and CLI surface. |
| Python implementation | not started | No `src/python/lpp/` package exists yet. |
| Test suite | not started | No implementation tests exist yet. |
| Comparator harness | not started | No comparator code or benchmark runner exists yet. |
| Exact benchmark oracle | not selected | Acceptable references are listed, but no implementation/version is frozen. |
| Calibration surface declaration | not started | Constants are named, but no calibration artifact exists in this repo. |
| Held-out benchmark evaluation | not started | No held-out tables or raw artifacts exist yet. |
| Sensitivity analysis | not started | No $\pm 10\%$ constant perturbation tables exist yet. |
| Cost measurement | not started | No timing harness or practicality evidence exists yet. |

## Supported Statements Right Now

At the current stage, the repository can support statements like:

- "The repository defines a closed-form seed and a deterministic refined predictor."
- "The current working seed uses the constants $c = -0.00016667$ and $\kappa^* = 0.065$."
- "The benchmark protocol requires deterministic families, declared oracles, and separate seed and refined tables."

It cannot yet support statements like:

- "The seed outperforms modern comparators."
- "The refined predictor is practically superior."
- "The calibrated advantage is robust."
- "The implementation reproduces the formula exactly."

## Next Validation Gates

The next validation gates are:

1. implement `lpp_seed`
2. implement `lpp_refined_predictor`
3. add direct formula and contract tests
4. select and record exact benchmark oracle implementations
5. emit first raw benchmark artifacts on held-out deterministic families

Until those gates are passed, the repository remains a specified research program rather than a validated software result.
