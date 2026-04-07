# API

This document defines the minimal public API and CLI contract for the Phase 3 reference implementation.

The contract is intentionally narrow. It covers only the predictor, its refined form, and version reporting.

## Python API

The reference package should expose:

```python
from lpp import get_version, lpp_refined_predictor, lpp_seed
```

### `lpp_seed`

```python
def lpp_seed(n: int) -> int:
    ...
```

Contract:

- input must be a Python integer
- input must satisfy $n \geq 5$
- output is a Python integer
- output is the rounded closed-form seed defined in [FORMULA.md](./FORMULA.md)
- rounding must follow the repository rule from [FORMULA.md](./FORMULA.md): nearest integer, with half-integers rounded upward

Error behavior:

- raise `TypeError` if `n` is not an integer
- raise `ValueError` if `n < 5`

The lower bound $n \geq 5$ is deliberate. The current logarithmic backbone becomes positive at $n = 5$, so the minimal contract begins at the first integer where the full closed-form seed is directly defined without a special-case branch.

### `lpp_refined_predictor`

```python
def lpp_refined_predictor(n: int) -> int:
    ...
```

Contract:

- input must be a Python integer
- input must satisfy $n \geq 5$
- output is a Python integer
- output is prime
- output is computed by the deterministic rule from [METHOD.md](./METHOD.md):

$$ lpp_refined_predictor(n) = \operatorname{nextPrime}\!\left(lpp_seed(n) - 1\right) $$

Error behavior:

- raise `TypeError` if `n` is not an integer
- raise `ValueError` if `n < 5`

### `get_version`

```python
def get_version() -> str:
    ...
```

Contract:

- returns the package version as a string
- takes no arguments
- performs no network access and no benchmark work

## CLI Contract

The minimal CLI should expose exactly three commands:

```text
lpp seed N
lpp refine N
lpp version
```

Behavior:

- `lpp seed N` prints the integer value of `lpp_seed(N)` followed by `\n`
- `lpp refine N` prints the integer value of `lpp_refined_predictor(N)` followed by `\n`
- `lpp version` prints the version string followed by `\n`

Error behavior:

- invalid input must produce a non-zero exit status
- invalid input should print a short human-readable error to standard error

## Non-Goals of the Minimal API

The minimal public API does not include:

- batch evaluation helpers
- comparator functions
- benchmark runners
- calibration tools
- plotting helpers
- alternative predictor families

Those may exist later as internal modules or benchmark-specific entrypoints, but they are outside the minimal public contract.

## Contract Notes

The reference implementation should make the rounding rule explicit in code rather than leaving it to language-default behavior. The repository contract is nearest-integer rounding with half-integers rounded upward.

## Stability Rule

Once the reference implementation lands, public names should remain:

- `lpp_seed`
- `lpp_refined_predictor`
- `get_version`

If the formula changes, the function names should stay fixed unless the repository deliberately introduces a versioned predictor identity and updates this document explicitly.
