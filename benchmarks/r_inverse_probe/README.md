# R-Inverse Seed Probe

This is a supporting exact probe, not the official top-level benchmark suite. The canonical repository benchmark now lives in [power_of_ten_anchor_suite](../power_of_ten_anchor_suite/README.md).

This probe tests a narrow question: whether a deterministic fixed-step inversion of the truncated Riemann prime-counting function can beat `li_inverse_seed` on the exact large-regime horizon already used in this repository.

This is a different category of object from the closed-form seed search. `r_inverse_seed` is an inversion seed, not a closed-form algebraic seed.

The construction is:

$$ p_n \approx R^{-1}(n) $$

with `R(x)` truncated at `K = 8` and solved by two fixed Newton steps starting from `cipolla_log5_repacked`.

$$ R(x) = \sum_{k=1}^{K} \frac{\mu(k)}{k}\operatorname{Li}(x^{1/k}) $$

$$ x \leftarrow x - \frac{R(x) - n}{R'(x)} $$

$$ R'(x) = \frac{1}{\ln x}\sum_{k=1}^{K} \frac{\mu(k)}{k}x^{1/k - 1} $$

## Strongest Finding

`r_inverse_seed` beats both `cipolla_log5_repacked` and `li_inverse_seed` on the exact anchors from `10^12` through `10^18`, and it also wins every exact stage family in `stage_a` and `stage_b`.

### stage_a

- `boundary_window` max ppm: `r_inverse_seed = 0.010704`, `li_inverse_seed = 0.048934`, `cipolla_log5_repacked = 0.033778`
- `dense_local_window` max ppm: `r_inverse_seed = 0.010706`, `li_inverse_seed = 0.089328`, `cipolla_log5_repacked = 0.070933`
- `off_lattice_decimal` max ppm: `r_inverse_seed = 0.010110`, `li_inverse_seed = 0.050585`, `cipolla_log5_repacked = 0.038038`

### stage_b

- `boundary_window` max ppm: `r_inverse_seed = 0.000304`, `li_inverse_seed = 0.005202`, `cipolla_log5_repacked = 0.000811`
- `dense_local_window` max ppm: `r_inverse_seed = 0.002678`, `li_inverse_seed = 0.010553`, `cipolla_log5_repacked = 0.005033`
- `off_lattice_decimal` max ppm: `r_inverse_seed = 0.000438`, `li_inverse_seed = 0.003699`, `cipolla_log5_repacked = 0.001466`

## Exact Anchor Comparison

- `10^12`: `cipolla_log5_repacked = 0.130786` ppm, `li_inverse_seed = 0.160206` ppm, `r_inverse_seed = 0.037259` ppm
- `10^14`: `cipolla_log5_repacked = 0.009349` ppm, `li_inverse_seed = 0.017581` ppm, `r_inverse_seed = 0.000508` ppm
- `10^15`: `cipolla_log5_repacked = 0.000527` ppm, `li_inverse_seed = 0.005202` ppm, `r_inverse_seed = 0.000304` ppm
- `10^16`: `cipolla_log5_repacked = 0.000811` ppm, `li_inverse_seed = 0.001948` ppm, `r_inverse_seed = 0.000267` ppm
- `10^17`: `cipolla_log5_repacked = 0.001219` ppm, `li_inverse_seed = 0.000465` ppm, `r_inverse_seed = 0.000050` ppm
- `10^18`: `cipolla_log5_repacked = 0.000884` ppm, `li_inverse_seed = 0.000174` ppm, `r_inverse_seed = 0.000016` ppm

## Artifacts

- [dataset_summary.csv](./dataset_summary.csv)
- [stage_family_summary.csv](./stage_family_summary.csv)
- [anchor_comparison.csv](./anchor_comparison.csv)
- [exact_anchor_comparison.png](./plots/exact_anchor_comparison.png)
- [exact_stage_family_max_ppm.png](./plots/exact_stage_family_max_ppm.png)
- [local_continuation_family_max_ppm.png](./plots/local_continuation_family_max_ppm.png)
