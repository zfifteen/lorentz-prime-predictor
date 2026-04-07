# Validation Status

This document records what has and has not been validated in the repository at the current stage.

## Current State

The repository now has a minimal reference implementation, direct API tests, an exact shipped contract grid, and an exact adversarial benchmark program with completed scaling stages through `stage_b`.

The active local workflow in this repository does not invoke `primecount`. Exact datasets are treated as committed artifacts, and local prediction work should use the workspace Z5D C implementation.

What is currently complete:

- the public vocabulary
- the origin narrative
- the closed-form seed definition
- the seed domain $n \geq 1$ and rounding contract
- the seed-versus-refined method distinction
- the benchmark protocol
- the public claim boundary
- the reference set for future implementation and benchmarking
- the intended public API contract
- the minimal Python reference implementation
- direct tests for the public API and CLI surface
- the shipped exact contract grid through $10^{24}$
- a Z5D-backed local `stage_c` continuation on $10^{17},10^{18}$

What is not yet complete:

- the broader research-grade test suite
- rank-error reporting
- sensitivity tables
- timing harness
- an exact external-label `stage_c` scaling dataset

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
| Comparator harness | complete | The off-lattice benchmark module implements the declared point-estimate comparator set for the held-out benchmark harness. |
| Exact contract-grid artifact | complete | The shipped $10^0,\dots,10^{24}$ grid is committed in `data/KNOWN_PRIMES.md` and consumed as a fixed exact artifact in local workflow. |
| Exact benchmark artifact beyond shipped grid | complete on committed stages | The held-out adversarial datasets through `stage_b` are committed and consumed as fixed exact artifacts in local workflow. |
| Z5D-backed local continuation | complete | A local `stage_c` dataset on $10^{17},10^{18}$ now exists using the workspace C Z5D predictor as the label source. |
| Calibration surface declaration | not started | Constants are named, but no calibration artifact exists in this repo. |
| Held-out benchmark evaluation | complete for exact stages through `stage_b` and local `stage_c` continuation | Exact adversarial artifacts now exist on $10^4,\dots,10^{12}$, $10^{13},10^{14}$, and $10^{15},10^{16}$, and a Z5D-backed local continuation now exists on $10^{17},10^{18}$. |
| Visualization suite | complete for exact stages through `stage_b` and local `stage_c` continuation | Deterministic plots exist for family, boundary, dense-window, and scaling behavior across the committed exact horizon plus the Z5D-backed local continuation. |
| Scaling answer program | complete through exact `stage_b`, with local `stage_c` continuation | The stage-aware benchmark now produces a mechanical conclusion across the exact committed horizon and the declared Z5D-backed local continuation. |
| Sensitivity analysis | not started | No $\pm 10\%$ constant perturbation tables exist yet. |
| Cost measurement | not started | No timing harness or practicality evidence exists yet. |

## Supported Statements Right Now

At the current stage, the repository can support statements like:

- "The repository defines a closed-form seed and a deterministic refined predictor."
- "The current working seed uses the constants $c = -0.00016667$ and $\kappa^* = 0.065$."
- "The benchmark protocol requires deterministic families, declared ground-truth sources, and separate seed and refined tables."
- "The repository contains a minimal Python implementation of `lpp_seed`, `lpp_refined_predictor`, and `get_version`."
- "The shipped runtime and contract-grid dataset are exact on $n = 10^0,\dots,10^{24}$."
- "The repository contains an exact held-out adversarial benchmark on $10^4,\dots,10^{12}$ for off-lattice and boundary-window families."
- "The active local workflow in this repository does not require `primecount`."
- "On the completed exact scaling stages through `stage_b`, `lpp_seed` does not retain the best worst-case seed ppm."
- "On the completed exact scaling stages through `stage_b`, `li_inverse_seed` has the best worst-case, mean, and median seed ppm in every scaling-stage family."
- "The repository contains a Z5D-backed local `stage_c` continuation on $10^{17},10^{18}$."
- "On the Z5D-backed local `stage_c` continuation, `lpp_seed` has the best worst-case seed ppm in every tested family."

It cannot yet support statements like:

- "The seed outperforms modern comparators on the completed exact scaling horizon."
- "The scaling answer is exact through `stage_c`."
- "The refined predictor is practically superior."
- "The calibrated advantage is robust."
- "The implementation is asymptotically superior."

## Next Validation Gates

The next validation gates are:

1. deepen the semantic test suite beyond the current direct API checks
2. decide whether to obtain an exact external-label `stage_c` source or keep the Z5D-backed continuation as the repository's local exploratory stage
3. add exact $\pi(x)$ support for rank-error reporting
4. add sensitivity artifacts required by the protocol
5. add timing artifacts required by the protocol

Until those gates are passed, the repository remains a specified research program rather than a validated software result.
