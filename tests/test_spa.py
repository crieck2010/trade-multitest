"""Tests for Hansen's SPA test."""

import numpy as np
import pytest

from trade_multitest import spa_test


def _noise_round(seed, n=250, k=8):
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 0.01, size=(n, k))


def test_pvalues_approx_uniform_under_null():
    # Same uniformity property as the Reality Check, fewer rounds for speed.
    M = 80
    pvals = [
        spa_test(_noise_round(s), n_boot=200, seed=s)["p_value"]
        for s in range(M)
    ]
    hist, _ = np.histogram(pvals, bins=10, range=(0, 1))
    assert np.all(hist >= 2), f"bins too empty: {hist}"
    assert np.all(hist <= 20), f"bins too full: {hist}"
    assert np.mean(np.array(pvals) < 0.05) <= 0.15


def test_detects_true_edge_with_better_power_than_noise():
    rng = np.random.default_rng(21)
    n, k = 500, 10
    R = rng.normal(0.0, 0.01, size=(n, k))
    R[:, 7] += 0.002
    out = spa_test(R, n_boot=500, seed=21)
    assert out["verdict"] == "validated"
    assert out["best_trial"] == 7
    # Studentised stats must be finite and match the argmax trial.
    assert len(out["t_stats"]) == k
    assert all(np.isfinite(out["t_stats"]))


def test_deterministic_given_seed():
    R = _noise_round(5)
    a = spa_test(R, n_boot=300, seed=42)
    b = spa_test(R, n_boot=300, seed=42)
    assert a["p_value"] == b["p_value"]


def test_recentering_threshold_documented():
    import math
    out = spa_test(_noise_round(3), n_boot=200, seed=3)
    assert out["recentering_threshold"] == pytest.approx(
        math.sqrt(2.0 * math.log(math.log(250)))
    )


def test_contract_shape():
    out = spa_test(_noise_round(9), n_boot=200, seed=9)
    assert out["test"] == "hansen_spa"
    assert 0.0 <= out["p_value"] <= 1.0
    assert out["verdict"] in ("validated", "invalidated")


def test_fail_closed():
    with pytest.raises(ValueError):
        spa_test(np.zeros((10, 3)), n_boot=200)  # zero variance
    with pytest.raises(ValueError):
        spa_test(_noise_round(1)[:5], n_boot=200)  # n < 8
    with pytest.raises(ValueError):
        spa_test(_noise_round(1), n_boot=50)
