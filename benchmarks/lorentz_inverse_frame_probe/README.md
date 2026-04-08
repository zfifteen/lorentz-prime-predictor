# Lorentz Inverse Frame Probe

This probe tests a narrow question on exact data only:

Can a small Lorentz-style residual model on top of the same `li_inverse_seed` backbone extrapolate better than a same-budget classical residual model?

The backbone is fixed:

- `base_li_inverse(n) = li_inverse_seed(n)`

The signed residual is measured on the backbone scale:

- `r(n) = (p_n - base_li_inverse(n)) / base_li_inverse(n)`

Two two-term frames are fit by least squares on exact training rows:

- `classical_inverse_frame`: `r_hat = a/log(x0) + b/log(x0)^2`
- `lorentz_inverse_frame`: `r_hat = c*(log(x0)/e^4)^2 + k*x0^(-1/3)`

The comparison is sequential and exact-only:

- fit on baseline exact, test on exact `stage_a`
- fit on baseline exact plus exact `stage_a`, test on exact `stage_b`

## Strongest Finding

The bare `li_inverse_seed` backbone stays strongest on the held-out exact stages in this first probe.

But the Lorentz-style residual frame extrapolates better than the same-budget classical residual frame on both exact held-out splits:

- baseline -> `stage_a` mean ppm: `classical_inverse_frame = 528.796908`, `lorentz_inverse_frame = 179.635594`
- baseline + `stage_a` -> `stage_b` mean ppm: `classical_inverse_frame = 173.701756`, `lorentz_inverse_frame = 19.514866`

That does not prove the Lorentz frame is the final inverse answer. It does show that, under a matched tiny residual budget, the Lorentz-style frame carries more of the deep exact structure forward than the classical residual frame does.

## Artifacts

- [split_summary.csv](./split_summary.csv)
- [family_summary.csv](./family_summary.csv)
- [fit_coefficients.csv](./fit_coefficients.csv)
- [rowwise_results.csv](./rowwise_results.csv)
- [heldout_stage_mean_ppm.png](./plots/heldout_stage_mean_ppm.png)
- [heldout_stage_family_max_ppm.png](./plots/heldout_stage_family_max_ppm.png)

