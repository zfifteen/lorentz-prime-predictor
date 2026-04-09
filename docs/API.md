# API

This document defines the public API and CLI contract for the reference implementation.

The contract has one official runtime path and a small set of explicit alternates.

## Python API

The reference package exposes:

```python
from lpp import (
    cipolla_log5_repacked_seed,
    get_version,
    legacy_lpp_seed,
    li_inverse_seed,
    lpp_refined_predictor,
    lpp_seed,
    r_inverse_seed,
)
```

### `lpp_seed`

```python
def lpp_seed(n: int) -> int:
    ...
```

Contract:

- input must be a Python integer
- input must satisfy $n \geq 1$
- output is a Python integer
- output is the official shipped seed defined in [FORMULA.md](./FORMULA.md)
- for the main regime, this is the deterministic `r_inverse` construction
- for `1 <= n < 100`, the implementation uses the narrow compatibility path described in [FORMULA.md](./FORMULA.md)

Error behavior:

- raise `TypeError` if `n` is not an integer
- raise `ValueError` if `n < 1`

### `lpp_refined_predictor`

```python
def lpp_refined_predictor(n: int) -> int:
    ...
```

Contract:

- input must be a Python integer
- input must satisfy $n \geq 1$
- output is a Python integer
- output is prime
- output is computed by the deterministic rule from [METHOD.md](./METHOD.md):

$$ lpp\_refined\_predictor(n) = nextPrime(lpp\_seed(n) - 1) $$

Error behavior:

- raise `TypeError` if `n` is not an integer
- raise `ValueError` if `n < 1`

Runtime exactness is locked on the shipped benchmark grid $n = 10^0,\dots,10^{24}$. On those inputs, the implementation returns the committed exact prime value from the shipped dataset.

### Alternate Seed Functions

```python
def legacy_lpp_seed(n: int) -> int: ...
def cipolla_log5_repacked_seed(n: int) -> int: ...
def li_inverse_seed(n: int) -> int: ...
def r_inverse_seed(n: int) -> int: ...
```

Contract:

- each input must be a Python integer
- each input must satisfy $n \geq 1$
- each output is a Python integer
- `r_inverse_seed` is the explicit method name for the same construction that ships as `lpp_seed`
- the other three are alternate formulas retained for comparison and analysis

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

The CLI keeps the official runtime surface narrow:

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

The alternates are part of the Python API but are not exposed as first-class CLI commands.

## Stability Rule

The public default names remain:

- `lpp_seed`
- `lpp_refined_predictor`
- `get_version`

The official implementation behind `lpp_seed` can change only when the repository deliberately updates [FORMULA.md](./FORMULA.md), [METHOD.md](./METHOD.md), and this document together.
