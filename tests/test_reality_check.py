"""Tests for White's Reality Check."""

import numpy as np
import pytest

from trade_multitest import reality_check


def _noise_round(seed, n=250, k=8):
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 0.01, size=(n, k))


def test_pvalues_approx_uniform_under_null():
    # Property: under the global null (pure noise vs zero benchmark),
    # Reality Check p-values must be approximately uniform. 150
    # independent rounds; each of 10 bins should hold a sane share.
    M = 150
    pvals = [
        reality_check(_noise_round(s), n_boot=200, seed=s)["p_value"]
        for s in range(M)
    ]
    hist, _ = np.histogram(pvals, bins=10, range=(0, 1))
    # Uniform => 15 per bin; allow wide tolerance for simulation noise.
    assert np.all(hist >= 5), f"bins too empty: {hist}"
    assert np.all(hist <= 30), f"bins too full: {hist}"
    # And the 5% rejection rate must be sane (not wildly conservative).
    assert np.mean(np.array(pvals) < 0.05) <= 0.15


def test_detects_true_edge():
    rng = np.random.default_rng(11)
    n, k = 500, 10
    R = rng.normal(0.0, 0.01, size=(n, k))
    R[:, 3] += 0.002  # one genuine edge
    out = reality_check(R, n_boot=500, seed=11)
    assert out["verdict"] == "validated"
    assert out["p_value"] < 0.05
    assert out["best_trial"] == 3


def test_deterministic_given_seed():
    R = _noise_round(5)
    a = reality_check(R, n_boot=300, seed=42)
    b = reality_check(R, n_boot=300, seed=42)
    assert a["p_value"] == b["p_value"]
    assert a["statistic"] == b["statistic"]


def test_benchmark_excess():
    rng = np.random.default_rng(12)
    n, k = 400, 6
    bench = rng.normal(0.0005, 0.01, n)
    R = bench[:, None] + rng.normal(0.0, 0.002, size=(n, k))  # track bench
    out = reality_check(R, benchmark=bench, n_boot=300, seed=12)
    assert out["verdict"] == "invalidated"  # no excess edge


def test_contract_shape():
    out = reality_check(_noise_round(9), n_boot=200, seed=9)
    assert out["test"] == "white_reality_check"
    assert 0.0 <= out["p_value"] <= 1.0
    assert out["verdict"] in ("validated", "invalidated")
    assert out["n_trials"] == 8 and out["n_obs"] == 250


def test_fail_closed():
    with pytest.raises(ValueError):
        reality_check(np.full((10, 3), np.nan), n_boot=200)
    with pytest.raises(ValueError):
        reality_check(_noise_round(1), n_boot=50)
    with pytest.raises(ValueError):
        reality_check(_noise_round(1), benchmark=np.zeros(5))
