# Validation Status

This document records what has and has not been validated in the repository at the current stage.

## Current State

The repository now has a minimal reference implementation, direct API tests, a published exact shipped contract grid, an official exact benchmark suite for the four main formulas on `10^1` through `10^18`, and a committed sensitivity artifact for the shipped `r_inverse_seed` launch path.

The retained category leaders are:

- `cipolla_log5_repacked` for the closed-form seed category
- `r_inverse_seed` for the deterministic inversion seed category

The shipped runtime default now follows that deterministic inversion leader through `lpp_seed`.

The active local workflow in this repository treats committed datasets as fixed artifacts. The official benchmark suite now uses only the published exact anchor class. The older stage-based materials remain in the repository as supporting artifacts, and local `stage_c` remains in the local continuation class.

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
- the shipped published exact contract grid through $10^{24}$
- the official exact power-of-ten anchor suite through $10^{18}$
- closed-form seed benchmark artifacts beyond the official suite
- deterministic inversion seed benchmark artifacts beyond the official suite
- a local `stage_c` continuation on $10^{17},10^{18}$
- sensitivity analysis for the shipped `r_inverse_seed` launch path

What is not yet complete:

- the broader research-grade test suite
- rank-error reporting
- timing harness
- a full exact off-anchor benchmark horizon through $10^{18}$

## Review Findings

Recent review findings and remediation status are tracked in [REVIEW_FINDINGS.md](./REVIEW_FINDINGS.md).

The first blocking issue in that pass was the stale oracle-script test path. It was addressed first so the default `pytest -q` validation path can stay green while the remaining portability and dependency-drift findings are tracked in one place.

## Status Table

| Area | Status | Notes |
|---|---|---|
| Conceptual framing | complete | [ORIGIN.md](./ORIGIN.md) and [README.md](../README.md) are aligned. |
| Formula specification | complete | [FORMULA.md](./FORMULA.md) fixes the shipped `lpp_seed`, its inverse construction, low-index compatibility rule, domain, and rounding rule. |
| Method specification | complete | [METHOD.md](./METHOD.md) fixes the shipped seed/refined separation. |
| Benchmark contract | complete | [BENCHMARK_PROTOCOL.md](./BENCHMARK_PROTOCOL.md) defines the evaluation rules. |
| Public claim boundary | complete | [CLAIMS.md](./CLAIMS.md) defines what the repo may and may not say. |
| Reference set | complete | [REFERENCES.md](./REFERENCES.md) records the baseline citation targets. |
| Public API contract | complete | [API.md](./API.md) defines the intended minimal Python and CLI surface. |
| Python implementation | complete | Minimal `src/python/lpp/` package and CLI are present. |
| Direct API tests | complete | Public API and CLI smoke tests exist under `tests/python/`. |
| Category summary | complete | [CANDIDATE_CATEGORIES.md](./CANDIDATE_CATEGORIES.md) records the retained leaders by category. |
| Test suite | in progress | Direct tests exist, but the broader semantic suite from the plan is not built yet. |
| Comparator harness | complete | The off-lattice benchmark module implements the declared point-estimate comparator set for the held-out benchmark harness. |
| Published exact contract-grid artifact | complete | The shipped $10^0,\dots,10^{24}$ grid is committed in `data/KNOWN_PRIMES.md` and backed by OEIS-published exact sources. |
| Official benchmark suite | complete | [benchmarks/power_of_ten_anchor_suite/README.md](../benchmarks/power_of_ten_anchor_suite/README.md) is now the canonical exact comparison surface for the repository on $10^1,\dots,10^{18}$. |
| Reproducible exact benchmark artifact beyond contract grid | complete on committed stages | The held-out adversarial datasets through `stage_b` are committed and consumed as reproducible exact artifacts in local workflow. |
| Closed-form category leader artifact | complete | `cipolla_log5_repacked` benchmark artifacts are committed under `benchmarks/cipolla_repacked_probe/`. |
| Deterministic inversion category leader artifact | complete | `r_inverse_seed` benchmark artifacts are committed under `benchmarks/r_inverse_probe/`. |
| Local continuation | complete | A local `stage_c` dataset on $10^{17},10^{18}$ now exists in the declared local continuation class. |
| Calibration surface declaration | not started | Constants are named, but no calibration artifact exists in this repo. |
| Supporting exact and local probes | complete in current committed scope | Reproducible exact adversarial artifacts exist through `stage_b`, and a local continuation exists on $10^{17},10^{18}$. These remain supporting artifacts rather than the canonical top-level suite. |
| Visualization suite | complete for the official anchor suite and current supporting probes | Deterministic plots exist for the official anchor suite, the retained category artifacts, and the declared local continuation. |
| Scaling notes for shipped `lpp_seed` | complete as historical support | The stage-specific interpretation docs remain available for the shipped `lpp_seed` program, but they are no longer the canonical benchmark view. |
| Sensitivity analysis | complete | `±10%` one-at-a-time perturbation tables and plots committed under `benchmarks/r_inverse_sensitivity/`. All 35 of 35 exact scenario summaries beat `li_inverse_seed` on worst-case seed ppm. Perturbations did not change exact family-summary maxima. |
| Cost measurement | not started | No timing harness or practicality evidence exists yet. |

## Supported Statements Right Now

At the current stage, the repository can support statements like:

- "The repository defines a closed-form seed and a deterministic refined predictor."
- "The legacy closed-form path uses the constants $c = -0.00016667$ and $\kappa^* = 0.065$."
- "For $n \geq 100$, the shipped `cipolla_log5_repacked_seed` uses repacked dynamic correction terms rather than those literal fixed constants."
- "`cipolla_log5_repacked` is the current retained leader in the closed-form seed category."
- "`r_inverse_seed` is the current retained leader in the deterministic inversion seed category."
- "`lpp_seed` now ships the deterministic `r_inverse` construction as the official runtime seed."
- "The official repository benchmark suite is the exact power-of-ten anchor suite on $10^1,\dots,10^{18}$."
- "The benchmark protocol requires deterministic families, declared ground-truth sources, and separate seed and refined tables."
- "The repository contains a minimal Python implementation of `lpp_seed`, `lpp_refined_predictor`, and `get_version`."
- "The shipped runtime and contract-grid dataset are published exact on $n = 10^0,\dots,10^{24}$."
- "On the official exact anchor suite, `lpp_seed` is sole best on 16 anchors and best-or-tied-best on 17 of the 18 anchors."
- "The repository contains reproducible exact held-out benchmark artifacts for the retained seed categories beyond the official suite."
- "The active local workflow consumes committed datasets as fixed artifacts."
- "The repository contains a local `stage_c` continuation on $10^{17},10^{18}$."
- "The local `stage_c` continuation is a separate provenance class and is not summarized as exact external evidence."
- "The shipped `r_inverse_seed` launch advantage is robust to `±10%` one-at-a-time perturbations of the repacked correction terms on the exact held-out surfaces tested."

It cannot yet support statements like:

- "One category leader replaces every other category in the repository."
- "`r_inverse_seed` is a closed-form formula."
- "The scaling answer is exact through `stage_c`."
- "The refined predictor is practically superior."
- "The implementation is asymptotically superior."

## Next Validation Gates

The next validation gates are:

1. deepen the semantic test suite beyond the current direct API checks
2. decide how much exact off-anchor horizon beyond the official anchor suite should become canonical, and what provenance rule that wider suite should require
3. add exact $\pi(x)$ support for rank-error reporting
4. add timing artifacts required by the protocol

Until those gates are passed, the repository remains a specified research program rather than a validated software result.
