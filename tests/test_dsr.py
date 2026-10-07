"""Tests for the Deflated Sharpe Ratio."""

import math

import numpy as np
import pytest

from trade_multitest import dsr, dsr_from_returns, expected_sharpe_null, moments
from trade_multitest._stats import norm_cdf, norm_ppf


def test_expected_null_zero_for_single_trial():
    assert expected_sharpe_null([1.5]) == 0.0


def test_expected_null_matches_formula():
    rng = np.random.default_rng(0)
    trials = rng.normal(0.5, 0.3, 20)
    k = 20
    g = 0.5772156649015329
    v = float(np.var(trials, ddof=1))
    ref = math.sqrt(v) * (
        (1 - g) * norm_ppf(1 - 1 / k) + g * norm_ppf(1 - 1 / (k * math.e))
    )
    assert expected_sharpe_null(trials) == pytest.approx(ref, rel=1e-9)


def test_expected_null_cross_checked_by_monte_carlo():
    # Independent check: the expected max of K iid standard-normal
    # Sharpes, estimated by simulation, must be near the analytic SR0
    # for unit-variance trials (trials standardised to unit variance).
    # Tolerance is loose on purpose: the published Bailey-Lopez
    # expression is a slightly conservative Gumbel approximation of
    # E[max], not the exact value — this test guards against gross
    # implementation error, not approximation error.
    rng = np.random.default_rng(1)
    k, sims = 50, 4000
    maxima = rng.normal(0.0, 1.0, size=(sims, k)).max(axis=1)
    trials = rng.normal(0.0, 1.0, size=k)
    trials = trials / trials.std(ddof=1)
    assert expected_sharpe_null(trials) == pytest.approx(maxima.mean(), abs=0.05)


def test_dsr_decreases_in_n_trials():
    # Property: same selected Sharpe, more trials from the same
    # dispersion -> lower DSR. (Padding with exact zeros is degenerate:
    # it collapses the trial variance, which legitimately shrinks SR0.)
    sr_hat = 1.2
    others = [0.4 * math.sin(i * 1.7) for i in range(76)]
    prev = 1.0
    for k in (1, 5, 20, 77):
        trials = [sr_hat] + others[: k - 1]
        p = dsr(sr_hat, trials, n_obs=1500)
        assert 0.0 <= p <= 1.0
        assert p <= prev + 1e-9, f"non-monotone at k={k}: {p} > {prev}"
        prev = p
    assert prev < 0.95  # 77 trials genuinely deflate a 1.2 Sharpe


def test_dsr_is_half_at_null_expectation():
    # Property: at sr_hat == SR0, DSR = Phi(0) = 0.5 exactly.
    trials = [0.4, -0.2, 0.1, 0.3, -0.1]
    sr0 = expected_sharpe_null(trials)
    assert dsr(sr0, trials, n_obs=1500) == pytest.approx(0.5, abs=1e-6)


def test_dsr_saturates_for_huge_sharpe():
    trials = [5.0] + [0.0] * 76
    assert dsr(5.0, trials, n_obs=1500) > 0.99


def test_dsr_near_zero_for_negative_sharpe():
    trials = [-1.5] + [0.0] * 10
    assert dsr(-1.5, trials, n_obs=1500) < 0.01


def test_dsr_honesty_single_trial_is_plain_test():
    # K=1: DSR reduces to 1 - p of Sharpe > 0 under normality.
    p = dsr(1.0, [1.0], n_obs=252)
    sr_d = 1.0 / math.sqrt(252)
    var_d = (1.0 + 0.5 * sr_d**2) / 252  # skew=0, kurt=3
    se = math.sqrt(var_d) * math.sqrt(252)
    assert p == pytest.approx(float(norm_cdf(1.0 / se)), rel=1e-6)


def test_dsr_from_returns_matches_manual():
    rng = np.random.default_rng(3)
    r = rng.normal(0.001, 0.01, 1000)
    trials = [1.0, 0.5, -0.2]
    m = moments(r)
    sr_hat = (m["mean"] / m["stdev"]) * math.sqrt(252)
    assert dsr_from_returns(r, trials) == pytest.approx(
        dsr(sr_hat, trials, m["n"], skew=m["skew"], kurt=m["kurt"]), rel=1e-9
    )


def test_moments_normal():
    rng = np.random.default_rng(4)
    m = moments(rng.normal(0.0, 1.0, 20000))
    assert m["skew"] == pytest.approx(0.0, abs=0.05)
    assert m["kurt"] == pytest.approx(3.0, abs=0.1)


def test_fail_closed():
    with pytest.raises(ValueError):
        dsr(1.0, [], n_obs=100)
    with pytest.raises(ValueError):
        dsr(float("nan"), [1.0], n_obs=100)
    with pytest.raises(ValueError):
        dsr(1.0, [1.0], n_obs=1)
    with pytest.raises(ValueError):
        dsr(1.0, [1.0], n_obs=100, skew=float("inf"))
    with pytest.raises(ValueError):
        moments([1.0, 1.0, 1.0])  # zero variance
