# Consistent n-scale Cipolla Repacked Probe

This probe tests one narrow question: whether a fully derived `k*(n)` can beat `li_inverse_seed` in the exact large regimes without introducing chosen coefficients.

The construction keeps the existing backbone form, but derives both the bend and the lift from the same `n`-scale Cipolla expansion.

Let

$$ L = \ln n $$

$$ \ell = \ln\ln n $$

$$ P(n) = n\left(L + \ell - 1 + \frac{\ell - 2}{L}\right) $$

The bend term is the exact `1/log^2 n` Cipolla correction routed through the existing bend slot:

$$ d(n) = -n\frac{\ell^2 - 6\ell + 11}{2L^2} $$

The order-5 candidate puts the next three Cipolla terms into the lift slot:

$$ P_3(\ell) = \frac{2\ell^3 - 21\ell^2 + 84\ell - 131}{6} $$

$$ P_4(\ell) = \frac{6\ell^4 - 92\ell^3 + 588\ell^2 - 1908\ell + 2666}{24} $$

$$ P_5(\ell) = \frac{24\ell^5 - 490\ell^4 + 4380\ell^3 - 22020\ell^2 + 62860\ell - 81534}{120} $$

$$ k_5^*(n) = \frac{n(P_3(\ell)/L^3 - P_4(\ell)/L^4 + P_5(\ell)/L^5)}{P(n)^{2/3}} $$

$$ \widehat{p}_n = round(P(n) + d(n) + k_5^*(n)P(n)^{2/3}) $$

This is algebraically the Cipolla asymptotic expansion through `1/log^5 n`, repacked into the existing backbone + bend + lift structure.

## Strongest Finding

The order-5 repacked seed is the first fully derived candidate in this line that beats `li_inverse_seed` on the exact large-regime stage families already committed in the repository.

- `stage_a` max seed ppm: `cipolla_log5_repacked = 0.070933`, `li_inverse_seed = 0.089328`
- `stage_b` max seed ppm: `cipolla_log5_repacked = 0.005033`, `li_inverse_seed = 0.010553`
- published exact grid max seed ppm: `cipolla_log5_repacked = 4163.125782`, `li_inverse_seed = 4382.740215`
- reproducible exact baseline max seed ppm: `cipolla_log5_repacked = 5050.456465`, `li_inverse_seed = 5271.714558`

Pointwise on the published power-of-ten grid, the order-5 repacked seed wins from `10^4` through `10^16` and then loses from `10^17` upward.

## Large-Regime Family Split

### stage_a

| family | order-5 max ppm | li max ppm | order-5 mean ppm | li mean ppm | order-5 median ppm | li median ppm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| boundary_window | 0.033778 | 0.048934 | 0.021563 | 0.033257 | 0.021562 | 0.033256 |
| dense_local_window | 0.070933 | 0.089328 | 0.029186 | 0.041800 | 0.023242 | 0.035048 |
| off_lattice_decimal | 0.038038 | 0.050585 | 0.009875 | 0.017588 | 0.007580 | 0.015647 |

### stage_b

| family | order-5 max ppm | li max ppm | order-5 mean ppm | li mean ppm | order-5 median ppm | li median ppm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| boundary_window | 0.000811 | 0.005202 | 0.000669 | 0.003575 | 0.000669 | 0.003575 |
| dense_local_window | 0.005033 | 0.010553 | 0.001724 | 0.004808 | 0.001053 | 0.003943 |
| off_lattice_decimal | 0.001466 | 0.003699 | 0.000991 | 0.001616 | 0.001089 | 0.001452 |

## Artifacts

- [dataset_summary.csv](./dataset_summary.csv)
- [stage_family_summary.csv](./stage_family_summary.csv)
- [published_point_comparison.csv](./published_point_comparison.csv)
- [dataset_max_ppm_by_variant.png](./plots/dataset_max_ppm_by_variant.png)
- [stage_family_max_ppm_order5_vs_li.png](./plots/stage_family_max_ppm_order5_vs_li.png)
- [published_points_order5_vs_li.png](./plots/published_points_order5_vs_li.png)
- [published_points_order5_vs_grok_revised.png](./plots/published_points_order5_vs_grok_revised.png)

