# Non-Heuristic Complexity Ladder

This probe tests a narrow question: how simple can a fully derived large-regime residual be before it stops beating `li_inverse_seed`?

The ladder is:

1. leading-log order 3
2. leading-log order 4
3. leading-log order 5
4. leading-log closed form
5. full repacked order 3
6. full repacked order 4
7. full repacked order 5

The leading-log family keeps only the highest-power `\ell^k/L^k` term from each Cipolla order, where `\ell = \ln\ln n` and `L = \ln n`.

The closed leading-log sum is

$$ u = \frac{\ln\ln n}{\ln n} $$

$$ n\left(\ln(1+u) - u + \frac{u^2}{2}\right) $$

The full repacked family keeps the exact Cipolla polynomials through the stated order.

## Strongest Finding

The first rung in this non-heuristic ladder that beats `li_inverse_seed` on both exact large stages is the full repacked order-5 candidate.

- `stage_b` max ppm, leading-log closed form: `10.689938`
- `stage_b` max ppm, full repacked order 4: `0.018887`
- `stage_b` max ppm, full repacked order 5: `0.005033`
- `stage_b` max ppm, `li_inverse_seed`: `0.010553`

So the large-stage win does not survive the leading-log simplification, and it does not survive the full order-4 truncation either. The exact first winning rung is full order 5.

## Artifacts

- [complexity_ladder_summary.csv](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/benchmarks/nonheuristic_complexity_ladder/complexity_ladder_summary.csv)
- [nonheuristic_complexity_ladder.png](/Users/velocityworks/IdeaProjects/lorentz-prime-predictor/benchmarks/nonheuristic_complexity_ladder/plots/nonheuristic_complexity_ladder.png)

