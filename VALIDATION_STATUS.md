# Validation Status

This document records what has and has not been validated in the repository at the current stage.

## Current State

The repository now has a minimal reference implementation and direct API tests, but it is still pre-benchmark and pre-validation as a comparative result.

What is currently complete:

- the public vocabulary
- the origin narrative
- the closed-form seed definition
- the seed domain $n \geq 5$ and rounding contract
- the seed-versus-refined method distinction
- the benchmark protocol
- the public claim boundary
- the reference set for future implementation and benchmarking
- the intended public API contract
- the minimal Python reference implementation
- direct tests for the public API and CLI surface

What is not yet complete:

- the broader research-grade test suite
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
| Python implementation | complete | Minimal `src/python/lpp/` package and CLI are present. |
| Direct API tests | complete | Public API and CLI smoke tests exist under `tests/python/`. |
| Test suite | in progress | Direct tests exist, but the broader semantic suite from the plan is not built yet. |
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
- "The repository contains a minimal Python implementation of `lpp_seed`, `lpp_refined_predictor`, and `get_version`."

It cannot yet support statements like:

- "The seed outperforms modern comparators."
- "The refined predictor is practically superior."
- "The calibrated advantage is robust."
- "The implementation reproduces the formula exactly."

## Next Validation Gates

The next validation gates are:

1. deepen the semantic test suite beyond the current direct API checks
2. select and record exact benchmark oracle implementations
3. implement comparator seeds
4. emit first raw benchmark artifacts on held-out deterministic families
5. add sensitivity and timing artifacts required by the protocol

Until those gates are passed, the repository remains a specified research program rather than a validated software result.
