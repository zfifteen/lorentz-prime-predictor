# Power-of-Ten Anchor Suite

Official exact benchmark suite for the repository.

This suite compares the four main formulas on `n = 10^1` through `10^18` using only exact power-of-ten anchors.

Ground-truth provenance: [data/KNOWN_PRIMES.md](../../data/KNOWN_PRIMES.md)

Formulas:
- `lpp_seed`
- `legacy_lpp_seed`
- `cipolla_log5_repacked_seed`
- `li_inverse_seed`

Strongest supported finding:
- `lpp_seed` is sole best on `16` anchors and best-or-tied-best on `17` anchors.
- This runtime now uses the deterministic `r_inverse` construction as the shipped seed path.

Artifacts:
- `rowwise_results.csv`: per-anchor per-formula exact results
- `formula_summary.csv`: aggregate exact metrics by formula
- `best_by_anchor.csv`: exact winner at each anchor
- `rank_by_anchor.csv`: exact rank ordering at each anchor

Status of older stage-based materials:
- exact and local stage-based probes remain in the repository as supporting research artifacts
- they are no longer the canonical benchmark surface for top-level summary or category decisions

Plots:
- `plots/anchor_rel_ppm.png`
- `plots/anchor_abs_error.png`
- `plots/anchor_rank.png`
