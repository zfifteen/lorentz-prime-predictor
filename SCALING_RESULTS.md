# Scaling Results

This document answers the main scaling question on the exact adversarial horizon that is currently completed in the repository.

## Direct Answer

The best current exact answer is:

$$
\text{the LPP seed advantage does not survive the completed scaling stages.}
$$

That statement is exact and bounded. It applies only to the committed completed horizon:

$$
10^4 \ldots 10^{12}, \qquad 10^{13} \ldots 10^{14}, \qquad 10^{15} \ldots 10^{16}.
$$

It does not say anything beyond that horizon.

## Mechanical Conclusion

The stage-aware benchmark uses a fixed mechanical rule:

- `survives strongly`
- `survives in the tail only`
- `does not survive`

On the completed scaling stages now committed in the repository, the result is:

`does not survive`

The reason is concrete. On every completed scaling-stage family cell, `lpp_seed` loses best worst-case seed ppm to `li_inverse_seed`.

## Stage Results

### Baseline

On the original exact adversarial baseline, `lpp_seed` still has the strongest worst-case seed ppm result in both declared families:

- `boundary_window`: `lpp_seed` max seed ppm `1250.589220`
- `off_lattice_decimal`: `lpp_seed` max seed ppm `651.648898`

That baseline result remains real.

### Stage A

Exact horizon:

$$
10^{13} \ldots 10^{14}
$$

Worst-case seed ppm winners:

- `boundary_window`: `li_inverse_seed` with `0.048934`
- `dense_local_window`: `li_inverse_seed` with `0.089328`
- `off_lattice_decimal`: `li_inverse_seed` with `0.050585`

LPP on the same cells:

- `boundary_window`: `38.935561`
- `dense_local_window`: `38.935561`
- `off_lattice_decimal`: `53.608778`

### Stage B

Exact horizon:

$$
10^{15} \ldots 10^{16}
$$

Worst-case seed ppm winners:

- `boundary_window`: `li_inverse_seed` with `0.005202`
- `dense_local_window`: `li_inverse_seed` with `0.010553`
- `off_lattice_decimal`: `li_inverse_seed` with `0.003699`

LPP on the same cells:

- `boundary_window`: `68.900290`
- `dense_local_window`: `68.900290`
- `off_lattice_decimal`: `82.532361`

## What Changed

At the baseline horizon, the LPP seed looked unusually strong on adversarial families.

At the deeper completed exact stages, that pattern reverses sharply. The inverse-log-integral seed is not merely slightly ahead. On worst-case seed ppm it is ahead by large ratios in every completed scaling-stage family.

The strongest ratio examples from the mechanical summary are:

- Stage A `off_lattice_decimal`: LPP / best-classical max-ppm ratio `1059.774449`
- Stage B `off_lattice_decimal`: LPP / best-classical max-ppm ratio `22312.597393`

## Best Supported Reading

The cleanest reading of the current evidence is:

- the baseline LPP win was real on the tested baseline horizon
- that win did not persist on the deeper completed exact scaling stages
- on the completed scaling horizon, the best seed is `li_inverse_seed`, not `lpp_seed`

## Figures

### Stage Seed Max ppm by Family

![Stage seed max ppm by family](./benchmarks/plots/off_lattice/stage_seed_max_ppm_by_family.png)

### Stage Seed Mean ppm by Family

![Stage seed mean ppm by family](./benchmarks/plots/off_lattice/stage_seed_mean_ppm_by_family.png)

### LPP vs Best Classical Ratio

![LPP vs best classical ratio](./benchmarks/plots/off_lattice/lpp_vs_best_classical_ratio.png)
