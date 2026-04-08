# c Derivation Probe

This probe compares the current baseline formula against one dynamic `c` variant while keeping `k* = 0.065` fixed. It also carries the strongest classical seed from the repository benchmarks:

- `fixed_c`: the current baseline with `c = -0.00016667`
- `asymptotic_c`: a derived dynamic `c(n)` from the next neglected nth-prime asymptotic term
- `li_inverse_seed`: the classical comparison seed, chosen because the repository's exact scaling benchmark through `stage_b` shows it has the best worst-case, mean, and median seed ppm in every scaling-stage family

The derived coefficient is

$$
c(n) = -\frac{e^8\left((\ln\ln P(n))^2 - 6\ln\ln P(n) + 11\right)}{2(\ln P(n))^5}.
$$

## Stage Summary

| Dataset | `fixed_c` max ppm | `asymptotic_c` max ppm | `li_inverse_seed` max ppm |
| --- | ---: | ---: | ---: |
| published exact grid (`n >= 10^4`) | 417.016424 | 1117.169074 | 4382.740215 |
| reproducible exact baseline | 1250.589220 | 1991.322835 | 5271.714558 |
| reproducible exact `stage_a` | 53.608778 | 11.091515 | 0.089328 |
| reproducible exact `stage_b` | 82.532361 | 5.856367 | 0.010553 |

The headline trade-off is simple:

- the fully dynamic derived `c(n)` is much better on `stage_a` and `stage_b`
- the same dynamic `c(n)` is much worse in the low regime
- `li_inverse_seed` remains the strongest classical comparator on the exact scaling stages, so it is the right classical line to keep in these runs

## Published Exact Grid By Scale

Selected exact point comparisons:

| `n` | `fixed_c` ppm | `asymptotic_c` ppm | `li_inverse_seed` ppm |
| ---: | ---: | ---: | ---: |
| `10^4` | 381.938145 | 1117.169074 | 4382.740215 |
| `10^5` | 417.016424 | 46.933583 | 1182.572407 |
| `10^8` | 172.623699 | 96.555340 | 24.688987 |
| `10^12` | 2.749147 | 14.464829 | 0.160206 |
| `10^18` | 97.402887 | 2.644104 | 0.000174 |
| `10^24` | 188.250606 | 0.950457 | 0.000000 |

Cutoff rollups from the published exact grid:

| start at `n` | `fixed_c` max ppm | `asymptotic_c` max ppm | `li_inverse_seed` max ppm |
| ---: | ---: | ---: | ---: |
| `10^4` | 417.016424 | 1117.169074 | 4382.740215 |
| `10^5` | 417.016424 | 190.057473 | 1182.572407 |
| `10^8` | 188.250606 | 96.555340 | 24.688987 |
| `10^10` | 188.250606 | 34.398575 | 2.541113 |
| `10^12` | 188.250606 | 14.464829 | 0.160206 |
| `10^18` | 188.250606 | 2.644104 | 0.000174 |
| `10^24` | 188.250606 | 0.950457 | 0.000000 |

## Artifacts

- [required_c_by_row.csv](./required_c_by_row.csv)
- [c_probe_rowwise.csv](./c_probe_rowwise.csv)
- [c_probe_summary.csv](./c_probe_summary.csv)
- [published_exact_point_comparison.csv](./published_exact_point_comparison.csv)
- [published_exact_cutoff_comparison.csv](./published_exact_cutoff_comparison.csv)
