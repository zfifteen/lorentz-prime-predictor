# Four-Formula Comparison

This benchmark suite compares four formulas on the repository's declared comparison horizon:

- `lpp_seed`
- `cipolla_log5_repacked`
- `r_inverse_seed`
- `li_inverse_seed`

The exact datasets are the published exact grid, the reproducible exact baseline, exact `stage_a`, and exact `stage_b`.
The local continuation dataset is reported separately as `stage_c local`.

## Strongest Findings

On the exact deep held-out stages, `r_inverse_seed` is the strongest candidate in this four-formula set.
- exact `stage_b` max ppm: `r_inverse_seed = 0.002678`, `li_inverse_seed = 0.010553`

On the local continuation off-anchor families, the picture flips because the labels come from the Z5D continuation family rather than exact primes.
- local `dense_local_window` max ppm: `lpp_seed = 0.000000000099`, `li_inverse_seed = 97.412202`
- local `off_lattice_decimal` max ppm: `lpp_seed = 0.000000000007`, `li_inverse_seed = 111.087273`

## Exact Anchor Snapshot

- `10^12`: `lpp_seed = 2.749147` ppm, `cipolla_log5_repacked = 0.130786` ppm, `r_inverse_seed = 0.037259` ppm, `li_inverse_seed = 0.160206` ppm
- `10^14`: `lpp_seed = 38.935561` ppm, `cipolla_log5_repacked = 0.009349` ppm, `r_inverse_seed = 0.000508` ppm, `li_inverse_seed = 0.017581` ppm
- `10^15`: `lpp_seed = 54.289695` ppm, `cipolla_log5_repacked = 0.000527` ppm, `r_inverse_seed = 0.000304` ppm, `li_inverse_seed = 0.005202` ppm
- `10^16`: `lpp_seed = 68.900290` ppm, `cipolla_log5_repacked = 0.000811` ppm, `r_inverse_seed = 0.000267` ppm, `li_inverse_seed = 0.001948` ppm
- `10^17`: `lpp_seed = 83.182716` ppm, `cipolla_log5_repacked = 0.001219` ppm, `r_inverse_seed = 0.000050` ppm, `li_inverse_seed = 0.000465` ppm
- `10^18`: `lpp_seed = 97.402887` ppm, `cipolla_log5_repacked = 0.000884` ppm, `r_inverse_seed = 0.000016` ppm, `li_inverse_seed = 0.000174` ppm

## Exact Family Snapshot

### stage_a

- `boundary_window` max ppm: `lpp_seed = 38.935561`, `cipolla_log5_repacked = 0.033778`, `r_inverse_seed = 0.010704`, `li_inverse_seed = 0.048934`
- `dense_local_window` max ppm: `lpp_seed = 38.935561`, `cipolla_log5_repacked = 0.070933`, `r_inverse_seed = 0.010706`, `li_inverse_seed = 0.089328`
- `off_lattice_decimal` max ppm: `lpp_seed = 53.608778`, `cipolla_log5_repacked = 0.038038`, `r_inverse_seed = 0.010110`, `li_inverse_seed = 0.050585`

### stage_b

- `boundary_window` max ppm: `lpp_seed = 68.900290`, `cipolla_log5_repacked = 0.000811`, `r_inverse_seed = 0.000304`, `li_inverse_seed = 0.005202`
- `dense_local_window` max ppm: `lpp_seed = 68.900290`, `cipolla_log5_repacked = 0.005033`, `r_inverse_seed = 0.002678`, `li_inverse_seed = 0.010553`
- `off_lattice_decimal` max ppm: `lpp_seed = 82.532361`, `cipolla_log5_repacked = 0.001466`, `r_inverse_seed = 0.000438`, `li_inverse_seed = 0.003699`

## Artifacts

- [dataset_summary.csv](./dataset_summary.csv)
- [stage_family_summary.csv](./stage_family_summary.csv)
- [anchor_comparison.csv](./anchor_comparison.csv)
- [rowwise_results.csv](./rowwise_results.csv)
- [dataset_mean_ppm.png](./plots/dataset_mean_ppm.png)
- [dataset_max_ppm.png](./plots/dataset_max_ppm.png)
- [exact_stage_family_max_ppm.png](./plots/exact_stage_family_max_ppm.png)
- [local_continuation_family_max_ppm.png](./plots/local_continuation_family_max_ppm.png)
- [exact_anchor_comparison.png](./plots/exact_anchor_comparison.png)

