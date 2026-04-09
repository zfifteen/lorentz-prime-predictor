# Formula

This document defines the shipped `lpp_seed` formula used by the reference implementation.

It is not the category-summary page for the repository's retained benchmark leaders. Those are tracked separately in [CANDIDATE_CATEGORIES.md](./CANDIDATE_CATEGORIES.md).

The deterministic forward step that turns the seed into a prime output is defined separately in [METHOD.md](./METHOD.md).

`lpp_seed` is now the repository's official deterministic inversion seed. The older closed-form `lpp_seed` line remains in the codebase as the alternate `legacy_lpp_seed`.

## Official Seed

For the main regime, the shipped seed is the fixed-step inverse construction

$$ lpp\_seed(n) = R^{-1}(n). $$

The counting model is the truncated Riemann prime-counting function

$$ R(x) = \sum_{k=1}^{8} \frac{\mu(k)}{k} Li(x^{1/k}). $$

The runtime starts from the repacked Cipolla seed and then applies exactly two Newton steps:

$$ x_0 = cipolla\_log5\_repacked\_seed(n) $$

$$ x_{j+1} = x_j - \frac{R(x_j) - n}{R'(x_j)} $$

with

$$ R'(x) = \frac{1}{\ln x}\sum_{k=1}^{8} \frac{\mu(k)}{k} x^{1/k - 1}. $$

The shipped seed output is the nearest integer to the final iterate, with half-integers rounded upward.

## Start Seed

The inversion path starts from the retained closed-form repacked Cipolla seed:

$$ P(n) = n\left(\ln n + \ln\ln n - 1 + \frac{\ln\ln n - 2}{\ln n}\right) $$

$$ \widehat{p}^{rep}_n = round(P(n) + d(n) + e(n)) $$

where the bend term comes from the repacked Cipolla correction and the lift term comes from the order-5 repacked residual.

The runtime uses that seed only as the deterministic launch point for inversion. It is not the final shipped seed contract.

## Low-Index Compatibility Path

The inverse construction is the official seed identity, but the implementation keeps a narrow compatibility rule for very small inputs.

For

$$ 1 \leq n < 100 $$

the shipped runtime returns `legacy_lpp_seed(n)`.

This keeps the public `n \geq 1` contract deterministic and avoids a low-index hole in the inverse path. The benchmark-critical regime begins well above that compatibility window.

## Alternates

The repository keeps three alternate seed formulas in code:

- `legacy_lpp_seed`
- `cipolla_log5_repacked_seed`
- `li_inverse_seed`

These are alternates for comparison and analysis. They are not the shipped default path anymore.
