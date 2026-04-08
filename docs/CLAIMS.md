# Claims

This document defines the public claim boundary for the repository. It exists so that README language, benchmark summaries, figures, release notes, and future papers all use the same evidence contract.

## Current Status

This repository supports narrow empirical claims, but only on the scopes and provenance classes already declared in the benchmark artifacts.

At the current stage, the repository supports:

- the current category split between closed-form seeds, deterministic inversion seeds, and refined prime-output methods
- the current retained closed-form leader `cipolla_log5_repacked`
- the current retained deterministic inversion leader `r_inverse_seed`
- the project name and public vocabulary
- the formula chosen for `lpp_seed`
- the method distinction between `lpp_seed` and `lpp_refined_predictor`
- the benchmark rules that comparative claims must satisfy
- reproducible exact comparative claims through `stage_b`
- local continuation claims on `stage_c`

Current documents may say that:

- `cipolla_log5_repacked` is the current best retained closed-form seed candidate
- `cipolla_log5_repacked` beats `li_inverse_seed` on exact `stage_a` and exact `stage_b`
- `cipolla_log5_repacked` leads through exact `10^16` and loses at exact `10^17` and exact `10^18`
- `r_inverse_seed` is the current best retained deterministic inversion seed candidate
- `r_inverse_seed` beats `li_inverse_seed` on exact anchors from `10^12` through `10^18`
- `r_inverse_seed` beats `li_inverse_seed` across every exact family in `stage_a` and `stage_b`
- the current local continuation stage is still a different provenance class and must not be summarized as exact external evidence

No current document should imply that:

- one category leader replaces another category leader
- `r_inverse_seed` is a closed-form algebraic seed
- the local continuation has the same evidence status as the published exact or reproducible exact stages
- the deterministic inversion result removes all implementation choices
- the refined predictor is already practically superior

## Claim Classes

### A. Definitional Claims

These claims are supported by repository documents alone.

| Claim | Required evidence |
|---|---|
| `lpp_seed` is the closed-form integer seed defined in [FORMULA.md](./FORMULA.md). | Formula document and later implementation parity tests. |
| `lpp_refined_predictor` is the deterministic forward refinement of that seed defined in [METHOD.md](./METHOD.md). | Method document and later implementation parity tests. |
| Seed and refined predictor are separate estimands. | [METHOD.md](./METHOD.md) and [BENCHMARK_PROTOCOL.md](./BENCHMARK_PROTOCOL.md). |

### B. Implementation-Parity Claims

These claims require code and tests.

| Claim | Required evidence |
|---|---|
| The reference implementation matches the formula in [FORMULA.md](./FORMULA.md). | Direct unit tests for each term, seed assembly, and rounding behavior. |
| The refined implementation matches the contract in [METHOD.md](./METHOD.md). | Direct unit tests for forward refinement and primality of returned outputs. |
| The public API is stable as documented. | Implemented functions and CLI behavior matching [API.md](./API.md), plus direct tests. |

### C. Closed-Form Seed Accuracy Claims

These claims concern a declared closed-form seed object.

| Claim | Required evidence |
|---|---|
| "Best mean ppm on family $F$." | Held-out seed table on declared family $F$, full declared point-estimate comparator set from [BENCHMARK_PROTOCOL.md](./BENCHMARK_PROTOCOL.md), declared ground-truth source, raw artifact, and summary artifact. |
| "Best median ppm on family $F$." | Same as above, with median ppm reported for every comparator. |
| "Best worst-case ppm on range $R$." | Same as above, with declared range $R$ and worst-case rows published. |
| "Smaller mean absolute rank error than comparator $X$." | Held-out seed table with exact $\pi(x)$ ground-truth source available on the declared horizon and aggregate rank-error statistics for both methods. |
| "Lower signed bias than comparator $X$." | Held-out seed table with mean signed error and sign ratio reported for both methods. |
| "Seed stays within the declared Axler or Dusart bound on range $R$." | Bound-validity table on declared range $R$, exact source citation, and explicit statement that the comparison is a bound check rather than a ppm ranking. |

The following are not sufficient for a seed-accuracy claim:

- calibration-set results alone
- sparse landmark grids alone when a dense deterministic family is required
- refined-output results
- plots without raw artifacts
- comparison against only weak baselines when the protocol requires the full declared point-estimate comparator set

### D. Refined Predictor Claims

These claims concern a declared refined prime-output object.

| Claim | Required evidence |
|---|---|
| "Best refined mean ppm on family $F$." | Held-out refined table on declared family $F$, shared refinement rule across predictors, declared ground-truth source, and raw artifact. |
| "Smaller refined rank error than comparator $X$." | Same, with exact $\pi(x)$ ground-truth source and aggregate rank-error statistics on the declared horizon. |
| "Useful launch point for deterministic prime output." | Separate seed and refined tables showing both seed proximity and refined-output behavior under the declared shared refinement rule. |

The following are not sufficient for a refined claim:

- a seed win by itself
- a refinement rule that differs across predictors
- anecdotes from a few hand-picked indices

### E. Practicality Claims

These claims require both accuracy and cost evidence.

| Claim | Required evidence |
|---|---|
| "Faster seed evaluation than comparator $X$." | Declared timing harness, hardware/software environment, batch timing results, and identical evaluation conditions for both methods. |
| "Faster full predictor than comparator $X$." | Same, but for the complete refined stack. |
| "Practically preferable on the declared workload." | Accuracy table on the declared workload plus the matching cost section required by [BENCHMARK_PROTOCOL.md](./BENCHMARK_PROTOCOL.md). |

Timing alone is not sufficient for a scientific superiority claim. Cost can support practicality language, but not accuracy language.

### F. Calibration-Robustness Claims

These claims require explicit sensitivity reporting.

| Claim | Required evidence |
|---|---|
| "The calibrated advantage is robust to small constant perturbations." | Held-out sensitivity tables for each calibrated constant at $-10\%$ and $+10\%$, with all other constants fixed. |
| "The advantage depends sharply on the chosen constants." | The same sensitivity tables, showing material degradation under small perturbation. |

## Unsupported Global Claims

The following claims are not supported by this repository unless a later document adds a strictly stronger evidence contract:

- "best formula in the literature"
- "asymptotically superior"
- "universally more accurate"
- "the definitive nth-prime formula"
- "physically derived proof of prime behavior"

## Writing Rule

Public prose should select the narrowest true claim, name the estimand, name the evaluated family or range, and state the comparator scope plainly.

Good examples:

- "best mean seed ppm on the dense deterministic interval family"
- "smaller refined rank error than comparator $X$ on the declared held-out horizon"
- "lower batch seed-evaluation time than comparator $X$ on the declared timing harness"

Bad examples:

- "best predictor"
- "more accurate in general"
- "state of the art"
