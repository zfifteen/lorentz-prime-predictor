# Scaling Interpretation

This note explains what the completed exact scaling results suggest, and what they do not prove.

## Concrete Result First

The completed exact scaling stages do not support the idea that the current LPP seed keeps its lead as the horizon rises.

On `stage_a` and `stage_b`, `li_inverse_seed` has the best worst-case, mean, and median seed ppm in every tested family:

- `boundary_window`
- `off_lattice_decimal`
- `dense_local_window`

That means the current best exact reading is not:

$$
\text{LPP found a stronger seed law that keeps beating the classical seeds as the horizon rises.}
$$

The current best exact reading is:

$$
\text{LPP was unusually strong on the baseline regime, but the deeper completed exact stages favor } \operatorname{li}^{-1}(n).
$$

## Tail Advantage

The main question in the scaling program was about worst-case seed ppm.

That answer is now clear on the completed horizon:

- baseline: `lpp_seed` wins the tail
- completed deeper stages: `li_inverse_seed` wins the tail

So the current LPP correction architecture does not keep the baseline tail advantage once the exact horizon is extended through the completed stages.

## Average Advantage

The average story is even less favorable to LPP on the completed scaling stages.

On `stage_a` and `stage_b`, `li_inverse_seed` also wins mean and median seed ppm in every family. So the deeper exact evidence does not merely take away the tail lead. It takes away the average lead as well.

## Boundary Structure

The boundary heatmaps are still useful. They show that LPP has coherent signed-error structure near decade transitions instead of chaotic noise.

That is interesting, but it is not enough on its own.

An orderly residual pattern can still be larger than a classical comparator's residual pattern. That is what the completed scaling stages now show.

## What This Suggests About the Correction Terms

The current correction architecture still appears to be doing something real in the baseline regime.

The log-squared pull still looks like a meaningful curvature correction to the Cipolla-style backbone. The sublinear lift still looks like a real residual-scale correction in the baseline range.

But the completed deeper exact stages suggest that these two fixed corrections do not track the deeper residual structure as well as the inverse-log-integral seed does.

The most natural reading is:

- the LPP corrections improved the backbone in a finite regime
- that improvement was not stable enough to beat `\operatorname{li}^{-1}(n)` on the deeper completed exact stages

## What Is Still Unproved

These results do not prove an asymptotic law either way.

They do not prove that LPP must always lose beyond the completed stages.
They do not prove that `\operatorname{li}^{-1}(n)` is universally best in every possible benchmark family.
They do not derive the LPP terms from RH, $\pi(x)-\operatorname{li}(x)$, or any explicit theorem in the repository.

They do show something narrower and important:

$$
\text{the strongest current exact evidence no longer supports the claim that the present LPP seed architecture scales best.}
$$

## Next Honest Moves

The honest next moves are now much narrower:

1. finish or replace the exact `stage_c` path
2. test whether a different fixed correction architecture can recover a tail lead on deeper exact stages
3. derive a theory-backed correction form instead of treating the current one as the final structure

Until then, the best current exact answer is the one already recorded in [SCALING_RESULTS.md](./SCALING_RESULTS.md).
