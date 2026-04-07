# Lorentz Prime Predictor

The Lorentz Prime Predictor is a first-principles research program for estimating the $n$th prime. It begins from one measurement idea: a quantity often becomes more legible when it is expressed against a fixed limit rather than read in isolation.

In relativity, that idea appears in the ratio $v/c$. In this repository, the same invariant-normalization logic is carried into number theory, used to build a closed-form seed for $p_n$, and then evaluated under a deterministic benchmark protocol.

## Public Objects

This repository defines three public objects:

- `lpp_seed`: the closed-form integer estimate for the $n$th prime
- `lpp_refined_predictor`: the seed followed by deterministic forward refinement to a prime output
- `benchmark protocol`: the rules that determine what this repository may and may not claim from its results

The seed and the refined predictor are separate estimands. Closed-form accuracy claims belong to `lpp_seed`. Prime-output utility claims belong to `lpp_refined_predictor`.

## Foundational Documents

- [ORIGIN.md](./ORIGIN.md): the Lorentz inspiration and the invariant-normalization bridge into number theory
- [FORMULA.md](./FORMULA.md): the closed-form seed, its constants, and the role of each term
- [METHOD.md](./METHOD.md): the distinction between the seed and the refined predictor
- [BENCHMARK_PROTOCOL.md](./BENCHMARK_PROTOCOL.md): the deterministic rules for comparison, artifacts, and claim language

## Research Contract Documents

- [CLAIMS.md](./CLAIMS.md): the exact claim boundary for public repository language
- [REFERENCES.md](./REFERENCES.md): the primary citation targets for formulas, comparators, and exact oracles
- [VALIDATION_STATUS.md](./VALIDATION_STATUS.md): what is and is not validated in the repository at the current stage
- [API.md](./API.md): the intended minimal Python and CLI contract for the reference implementation

## Scientific Position

The repository does not claim that relativistic physics is being imported into arithmetic as physics. The narrower claim is structural: invariant-normalized measurement suggests a useful way to organize nth-prime estimation.

Whether that idea yields practically strong accuracy is a benchmark question, not a naming assumption. For that reason, the repository defines the benchmark protocol before making large comparative claims.

The shipped runtime contract is exact on the committed power-of-ten grid

$$ n = 10^0,\dots,10^{24}. $$

Outside that shipped grid, the refined predictor remains a deterministic prime output built from the closed-form seed.

## Local Engine Policy

This repository no longer uses `primecount` in the active local workflow.

- exact contract and held-out datasets are consumed as committed artifacts
- local prediction work should use the C Z5D predictor in the workspace project at `../archive/z5d-prime-predictor/src/c/z5d-predictor-c`
- historical manifests that mention `primecount` remain as provenance for already committed exact datasets

## Current Stage

The repository is still intentionally narrow. The conceptual framing and research contract are fixed, a minimal Python reference implementation exists, exact adversarial benchmark artifacts now exist on a completed scaling horizon through `stage_b`, and the active local workflow now treats committed exact datasets as fixed inputs rather than regenerating them with heavyweight oracle tooling.

## Best Current Exact Answer

The strongest exact answer currently supported by this repository is:

$$
\text{No.}
$$

On the completed exact scaling stages now committed in the repository, `lpp_seed` does **not** retain the best worst-case seed ppm once the horizon rises past the original $10^4 \ldots 10^{12}$ benchmark.

- On the original baseline exact adversarial harness, `lpp_seed` had the best worst-case seed ppm in both families.
- On the completed scaling stages `stage_a` and `stage_b`, `li_inverse_seed` wins worst-case seed ppm in every tested family:
  - `boundary_window`
  - `off_lattice_decimal`
  - `dense_local_window`
- The same comparator also wins mean and median seed ppm in every completed scaling-stage family.

The completed exact horizon currently available for this answer is:

$$
10^4 \ldots 10^{12}, \qquad 10^{13} \ldots 10^{14}, \qquad 10^{15} \ldots 10^{16}.
$$

The direct benchmark artifacts are:

- [benchmarks/off_lattice_benchmark.md](./benchmarks/off_lattice_benchmark.md)
- [SCALING_RESULTS.md](./SCALING_RESULTS.md)
- [SCALING_INTERPRETATION.md](./SCALING_INTERPRETATION.md)

The lead figure is:

![Stage seed max ppm by family](./benchmarks/plots/off_lattice/stage_seed_max_ppm_by_family.png)
