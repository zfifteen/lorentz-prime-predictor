# Asymptotic-c Regularized Backbone-ratio Seed

This note describes a closed-form seed for the $n$th prime from a clean implementation point of view.

The construction has three pieces:

- a classical backbone $P(n)$
- a downward bend $d(n)$
- an upward lift $e(n)$

The seed is the nearest integer to the sum of those three pieces.

## 1. Backbone

Start with the explicit asymptotic backbone

$$
P(n) = n\left(\ln n + \ln\ln n - 1 + \frac{\ln\ln n - 2}{\ln n}\right)
$$

This is the first estimate of where the $n$th prime should sit.

It is useful to name the logarithmic factor by itself:

$$
B(n) = \frac{P(n)}{n}
$$

so

$$
B(n) = \ln n + \ln\ln n - 1 + \frac{\ln\ln n - 2}{\ln n}
$$

$B(n)$ is the backbone density. It says how much prime value the backbone assigns per unit of index.

## 2. Downward Bend

The backbone leaves out the next classical curvature term. The bend restores that missing part.

Write the bend in the LPP shape

$$
d(n) = c(n)P(n)\left(\frac{\ln P(n)}{e^4}\right)^2
$$

and choose $c(n)$ so this bend matches the next omitted asymptotic correction.

That gives

$$
c(n) = -\frac{e^8\left((\ln\ln P(n))^2 - 6\ln\ln P(n) + 11\right)}{2(\ln P(n))^5}
$$

So $c(n)$ is not a frozen decimal knob here. It is the value required by the next asymptotic bend of the classical expansion.

In ordinary language:

- $P(n)$ gives the main location
- $c(n)$ determines how much missing curvature must be restored
- $d(n)$ applies that curvature in the seed's multiplicative shape

## 3. Upward Lift

Once the bend is made asymptotic, the low regime can become too negative. The lift adds a controlled upward counterweight.

Keep the same power-law shape:

$$
e(n) = \kappa^*(n)P(n)^{2/3}
$$

The question is how to choose $\kappa^*(n)$ without hard-coding a decimal constant and without introducing a pole.

Use the backbone density $B(n)$ directly, but regularize the inverse structure so it stays finite:

$$
\kappa^*(n) = \frac{B(n) + e^2}{e^2\left(2B(n) + e^2\right)}
$$

This is the same as

$$
\kappa^*(n) = \frac{1}{e^2\left(2 - \frac{e^2}{B(n) + e^2}\right)}
$$

but the rational form is the cleaner implementation form.

This expression uses only structural ingredients already present in the method:

- the fixed prime count $2$
- the invariant normalization constant $e^2$
- the backbone density $B(n)$

It also has the behavior we want:

- when $B(n)$ is smaller, $\kappa^*(n)$ is a little larger
- when $B(n)$ grows, $\kappa^*(n)$ decays gently
- as scale grows, $\kappa^*(n)$ approaches a constant

At large scale,

$$
\kappa^*(n) \to \frac{1}{2e^2}
$$

For positive $B(n)$, the regularized ratio is bounded:

$$
\frac{1}{2e^2} < \kappa^*(n) < \frac{1}{e^2}
$$

So the lift stays finite, stays positive, and cannot blow up.

## 4. Full Seed

Put the three parts together:

$$
\widehat{p}_n = \left\lfloor P(n) + d(n) + e(n) + \frac{1}{2} \right\rfloor
$$

with

$$
P(n) = n\left(\ln n + \ln\ln n - 1 + \frac{\ln\ln n - 2}{\ln n}\right)
$$

$$
d(n) = c(n)P(n)\left(\frac{\ln P(n)}{e^4}\right)^2
$$

$$
c(n) = -\frac{e^8\left((\ln\ln P(n))^2 - 6\ln\ln P(n) + 11\right)}{2(\ln P(n))^5}
$$

$$
e(n) = \kappa^*(n)P(n)^{2/3}
$$

$$
\kappa^*(n) = \frac{B(n) + e^2}{e^2\left(2B(n) + e^2\right)}
$$

$$
B(n) = \frac{P(n)}{n}
$$

## 5. Implementation Recipe

The implementation is a straight-line computation.

1. Compute $L = \ln n$.
2. Compute $LL = \ln L$.
3. Compute

$$
B = L + LL - 1 + \frac{LL - 2}{L}
$$

4. Compute $P = nB$.
5. Compute $LP = \ln P$ and $LLP = \ln LP$.
6. Compute

$$
c = -\frac{e^8(LLP^2 - 6LLP + 11)}{2LP^5}
$$

7. Compute

$$
d = cP\left(\frac{LP}{e^4}\right)^2
$$

8. Compute

$$
\kappa = \frac{B + e^2}{e^2(2B + e^2)}
$$

9. Compute

$$
e = \kappa P^{2/3}
$$

10. Return the nearest integer to $P + d + e$.

In Python-like pseudocode:

```python
from math import e, floor, log


def regularized_backbone_ratio_seed(n: int) -> int:
    L = log(n)
    LL = log(L)
    B = L + LL - 1.0 + (LL - 2.0) / L
    P = n * B

    LP = log(P)
    LLP = log(LP)

    c = -(e**8) * (LLP**2 - 6.0 * LLP + 11.0) / (2.0 * LP**5)
    d = c * P * (LP / (e**4))**2

    kappa = (B + e**2) / (e**2 * (2.0 * B + e**2))
    lift = kappa * P**(2.0 / 3.0)

    return floor(P + d + lift + 0.5)
```

## 6. What Is Closed-form Here

This seed is closed-form in the ordinary sense:

- finite explicit formula
- no iteration
- no lookup table
- no fitted decimal constants inserted by calibration

That does not make it an exact formula for $p_n$. It is a closed-form seed.

## 7. Domain

The bend term uses $\ln P(n)$ and $\ln\ln P(n)$, so the construction needs

$$
P(n) > 1
$$

For this backbone, that begins at integer input

$$
n \geq 6
$$

From that point onward:

- $B(n)$ is positive
- $2B(n) + e^2$ is positive
- $\kappa^*(n)$ is finite
- the lift stays positive

So this repaired lift has no internal pole on its valid integer domain.

The tracked probe results for this construction are in the large-scale regime beginning at $n=10^4$.

## 8. Status

This note describes a probe formula currently tracked in [k_probe_summary.csv](../benchmarks/k_derivation_probe/k_probe_summary.csv) and the related artifacts under [benchmarks/k_derivation_probe](../benchmarks/k_derivation_probe).

Its role is narrow: give a clean, auditable implementation of the asymptotic-$c$ plus regularized backbone-ratio-$\kappa^*$ construction.
