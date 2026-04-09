# R-Inverse Sensitivity Probe

This artifact tests calibration-robustness for the shipped `r_inverse_seed` launch path.

It perturbs the repacked launch correction terms one at a time by `-10%` and `+10%`, keeps the Newton loop fixed, and compares each scenario against `li_inverse_seed`.

## Strongest Finding

`the shipped launch advantage is robust on the exact held-out surfaces tested`

Across the tested exact family cells, `35` of `35` scenario summaries still beat `li_inverse_seed` on worst-case seed ppm.

The `-10%` and `+10%` one-at-a-time perturbations did not change the exact family-summary maxima in this run.

On local `stage_c`, the same perturbations remain diagnostic only and the summary still does not favor `r_inverse_seed` over `li_inverse_seed`.

The headline exact evidence uses only:

- the official exact anchor suite through `10^18`
- reproducible exact `stage_a`
- reproducible exact `stage_b`

The local `stage_c` continuation is included only as a diagnostic appendix and is not used as headline exact evidence.

## Artifacts

- [rowwise_results.csv](./rowwise_results.csv)
- [family_summary.csv](./family_summary.csv)
- [anchor_summary.csv](./anchor_summary.csv)
- [plots/exact_family_max_ppm.png](./plots/exact_family_max_ppm.png)
- [plots/local_stage_c_family_max_ppm.png](./plots/local_stage_c_family_max_ppm.png)
- [plots/exact_anchor_sensitivity.png](./plots/exact_anchor_sensitivity.png)
