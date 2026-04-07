# Formula

This document defines the closed-form seed of the Lorentz Prime Predictor. The deterministic forward step that turns the seed into a prime output is defined separately in [METHOD.md](./METHOD.md).

In this repository, the seed contract begins at $n \geq 5$.

The asymptotic backbone is

$$ P(n) = n\left(\ln n + \ln\ln n - 1 + \frac{\ln\ln n - 2}{\ln n}\right) $$

The predictor then applies two calibrated corrections:

$$ d(n) = c P(n)\left(\frac{\ln P(n)}{e^4}\right)^2 $$

$$ e(n) = \kappa^* P(n)^{2/3} $$

The closed-form seed is

$$ \widehat{p}_n = round(P(n) + d(n) + e(n)) $$

Here $round(x)$ means nearest-integer rounding with half-integers rounded upward. Since the predictor is evaluated only for positive $n$, this is the same as $\lfloor x + 1/2 \rfloor$.

The current working constants are

$$ c = -0.00016667,\ \kappa^* = 0.065 $$

## Interpretation of the Terms

$P(n)$ sets the main scale. It is the asymptotic backbone for the $n$th prime.

$d(n)$ is a negative logarithmic correction. It scales with $P(n)$ and grows with the squared factor $\left(\ln P(n)/e^4\right)^2$. Its role is to bend the backbone downward where the raw asymptotic term sits systematically high.

$e(n)$ is a positive sublinear lift. Because it grows like $P(n)^{2/3}$, it is large enough to matter in practical regimes while remaining smaller than the main scale of $P(n)$.

Taken together, the seed has the form

`backbone + negative logarithmic correction + positive sublinear lift`

## Compact Seed Form

Using the shorthand $P(n)$, the seed can be written in one display as

$$ \widehat{p}_n = round\left(n\left(\ln n + \ln\ln n - 1 + \frac{\ln\ln n - 2}{\ln n}\right) + c P(n)\left(\frac{\ln P(n)}{e^4}\right)^2 + \kappa^* P(n)^{2/3}\right) $$

## Naming

This repository uses `lpp_seed` for the closed-form quantity $\widehat{p}_n$ and `lpp_refined_predictor` for the deterministic prime output obtained from that seed.

This document concerns only `lpp_seed`. The forward search rule belongs to [METHOD.md](./METHOD.md).
