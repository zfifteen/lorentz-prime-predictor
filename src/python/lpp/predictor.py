from __future__ import annotations

import math

import gmpy2 as gp
import mpmath as mp
from sympy import mobius


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
_CIPOLLA_RAW_POLYNOMIALS = {
    3: (-131, 84, -21, 2),
    4: (2666, -1908, 588, -92, 6),
    5: (-81534, 62860, -22020, 4380, -490, 24),
}


def _require_index(n: int) -> int:
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 1:
        raise ValueError("n must be >= 1")
    return n


def _round_half_up_positive(x: gp.mpfr) -> int:
    return int(gp.mpz(x + 0.5))


def _basis_row(n: int) -> dict[str, float]:
    precision = max(2048, int(gp.log2(n)) + 2048)
    with gp.context(gp.get_context(), precision=precision):
        n_mp = gp.mpfr(n)
        ln_n = gp.log(n_mp)
        ln_ln_n = gp.log(ln_n)
        p_n = n_mp * (ln_n + ln_ln_n - 1 + ((ln_ln_n - 2) / ln_n))
        if p_n <= 0:
            p_n = n_mp
        ln_p = gp.log(p_n)
        return {
            "P": float(p_n),
            "L": float(ln_n),
            "LL": float(ln_ln_n),
            "LP": float(ln_p),
            "B": float(p_n / n_mp),
        }


def _c_n_value(basis_row: dict[str, float]) -> float:
    ln_n = basis_row["L"]
    ln_ln_n = basis_row["LL"]
    ln_p = basis_row["LP"]
    backbone_ratio = basis_row["B"]
    poly2 = (ln_ln_n**2) - 6.0 * ln_ln_n + 11.0
    return -poly2 / (2.0 * (ln_n**2) * backbone_ratio * ((ln_p / (math.e**4)) ** 2))


def _cipolla_polynomial(order: int, ln_ln_n: float) -> float:
    coefficients = _CIPOLLA_RAW_POLYNOMIALS[order]
    total = 0.0
    for power, coefficient in enumerate(coefficients):
        total += coefficient * (ln_ln_n**power)
    return total / math.factorial(order)


def _repacked_kappa_order5(basis_row: dict[str, float]) -> float:
    pnt = basis_row["P"]
    ln_n = basis_row["L"]
    ln_ln_n = basis_row["LL"]
    n_value = pnt / basis_row["B"]
    residual = 0.0
    for order in range(3, 6):
        sign = 1.0 if order % 2 == 1 else -1.0
        residual += n_value * sign * _cipolla_polynomial(order, ln_ln_n) / (ln_n**order)
    return residual / (pnt ** (2.0 / 3.0))


def _riemann_r(x_value: mp.mpf, truncation_k: int) -> mp.mpf:
    total = mp.mpf("0")
    for k_value in range(1, truncation_k + 1):
        mu_value = mobius(k_value)
        if mu_value == 0:
            continue
        total += mp.mpf(mu_value) / k_value * mp.li(x_value ** (mp.mpf(1) / k_value))
    return total


def _riemann_r_derivative(x_value: mp.mpf, truncation_k: int) -> mp.mpf:
    total = mp.mpf("0")
    for k_value in range(1, truncation_k + 1):
        mu_value = mobius(k_value)
        if mu_value == 0:
            continue
        total += mp.mpf(mu_value) / k_value * (x_value ** (mp.mpf(1) / k_value - 1))
    return total / mp.log(x_value)


def legacy_lpp_seed(n: int) -> int:
    n = _require_index(n)
    if n < 2:
        return 2

    precision = max(2048, int(gp.log2(n)) + 2048)
    with gp.context(gp.get_context(), precision=precision):
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


def cipolla_log5_repacked_seed(n: int) -> int:
    n = _require_index(n)
    if n < 100:
        return legacy_lpp_seed(n)

    basis_row = _basis_row(n)
    pnt = basis_row["P"]
    ln_p = basis_row["LP"]
    c_value = _c_n_value(basis_row)
    d_value = c_value * pnt * ((ln_p / (math.e**4)) ** 2)
    kappa = _repacked_kappa_order5(basis_row)
    estimate = pnt + d_value + kappa * (pnt ** (2.0 / 3.0))
    return math.floor(estimate + 0.5)


def li_inverse_seed(n: int) -> int:
    n = _require_index(n)
    if n < 10:
        return legacy_lpp_seed(n)

    mp.mp.dps = 100
    ln_n = math.log(n)
    ln_ln_n = math.log(ln_n)
    start = n * (ln_n + ln_ln_n - 1.0 + (ln_ln_n - 2.0) / ln_n)
    seed = mp.mpf(start)
    target = mp.mpf(n)
    for _ in range(8):
        seed -= (mp.li(seed) - target) * mp.log(seed)
    return int(gp.mpz(seed + 0.5))


def r_inverse_seed(n: int, truncation_k: int = 8, newton_steps: int = 2) -> int:
    n = _require_index(n)
    if n < 100:
        return legacy_lpp_seed(n)

    mp.mp.dps = 100
    x_value = mp.mpf(cipolla_log5_repacked_seed(n))
    target = mp.mpf(n)
    for _ in range(newton_steps):
        x_value -= (_riemann_r(x_value, truncation_k) - target) / _riemann_r_derivative(x_value, truncation_k)
    return int(gp.mpz(x_value + 0.5))


def lpp_seed(n: int) -> int:
    return r_inverse_seed(n)


def lpp_refined_predictor(n: int) -> int:
    n = _require_index(n)
    if n in _KNOWN_PRIMES:
        return _KNOWN_PRIMES[n]
    seed = lpp_seed(n)
    return int(gp.next_prime(seed - 1))
