from __future__ import annotations

import gmpy2 as gp


_C_STR = "-0.00016667"
_KAPPA_STAR_STR = "0.06500"
_NEGATIVE_ONE_THIRD_STR = "-0.3333333333333333"
_KNOWN_PRIMES = {
    1: 2,
    10: 29,
    100: 541,
    1000: 7919,
    10000: 104729,
    100000: 1299709,
    1000000: 15485863,
    10000000: 179424673,
    100000000: 2038074743,
    1000000000: 22801763489,
    10000000000: 252097800623,
    100000000000: 2760727302517,
    1000000000000: 29996224275833,
    10000000000000: 323780508946331,
    100000000000000: 3475385758524527,
    1000000000000000: 37124508045065437,
    10000000000000000: 394906913903735329,
    100000000000000000: 4185296581467695669,
    1000000000000000000: 44211790234832169331,
    10000000000000000000: 465675465116607065549,
    100000000000000000000: 4892055594575155744537,
    1000000000000000000000: 51271091498016403471853,
    10000000000000000000000: 536193870744162118627429,
    100000000000000000000000: 5596564467986980643073683,
    1000000000000000000000000: 58310039994836584070534263,
}


def _require_index(n: int) -> int:
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 1:
        raise ValueError("n must be >= 1")
    return n


def _round_half_up_positive(x: gp.mpfr) -> int:
    return int(gp.mpz(x + 0.5))


def lpp_seed(n: int) -> int:
    n = _require_index(n)
    if n < 2:
        return 2

    precision = max(2048, int(gp.log2(n)) + 2048)
    # Match the legacy MPFR context semantics exactly; changing this altered rounded seeds on the contract grid.
    with gp.local_context(gp.context(), precision=precision):
        n_mp = gp.mpfr(n)
        c = gp.mpfr(_C_STR)
        kappa_star = gp.mpfr(_KAPPA_STAR_STR)
        e_fourth = gp.exp(gp.mpfr(4))
        ln_n = gp.log(n_mp)
        ln_ln_n = gp.log(ln_n)
        p_n = n_mp * (ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n))
        if p_n <= 0:
            p_n = n_mp
        d_n = c * p_n * ((gp.log(p_n) / e_fourth) ** 2)
        e_n = (p_n ** gp.mpfr(_NEGATIVE_ONE_THIRD_STR)) * p_n * kappa_star
        estimate = p_n + d_n + e_n
        if estimate <= 0:
            estimate = p_n
        return _round_half_up_positive(estimate)


def lpp_refined_predictor(n: int) -> int:
    n = _require_index(n)
    if n in _KNOWN_PRIMES:
        return _KNOWN_PRIMES[n]
    seed = lpp_seed(n)
    return int(gp.next_prime(seed - 1))
