"""Tests for the Holm step-down procedure."""

import numpy as np
import pytest

from trade_multitest import holm, t_test_pvalues


def test_holm_controls_fwer_under_global_null():
    # Property: with all nulls true, P(any rejection) <= alpha.
    rng = np.random.default_rng(31)
    M, m, alpha = 300, 10, 0.05
    false_rounds = 0
    for s in range(M):
        p = rng.random(m)  # uniform p-values under the global null
        if holm(p, alpha)["n_rejected"] > 0:
            false_rounds += 1
    assert false_rounds / M <= alpha + 0.03


def test_holm_detects_true_effects():
    p = [0.001, 0.002, 0.4, 0.5, 0.9]
    out = holm(p, alpha=0.05)
    assert out["reject"] == [True, True, False, False, False]
    assert out["verdicts"][:2] == ["validated", "validated"]
    assert out["verdicts"][2] == "invalidated"


def test_holm_adjusted_pvalues_monotone():
    rng = np.random.default_rng(32)
    p = rng.random(15)
    out = holm(p)
    order = np.argsort(p, kind="stable")
    adj_sorted = np.array(out["p_adjusted"])[order]
    assert np.all(np.diff(adj_sorted) >= 0)
    assert np.all((np.array(out["p_adjusted"]) >= p - 1e-12))
    assert np.all(np.array(out["p_adjusted"]) <= 1.0)


def test_holm_more_powerful_than_bonferroni():
    # Holm rejects a superset of Bonferroni rejections.
    rng = np.random.default_rng(33)
    for _ in range(50):
        p = rng.random(8)
        h = holm(p, 0.05)["reject"]
        b = [x <= 0.05 / 8 for x in p]
        assert all((not bb) or hh for bb, hh in zip(b, h))


def test_t_test_pvalues_detects_edge():
    rng = np.random.default_rng(34)
    n = 500
    R = rng.normal(0.0, 0.01, size=(n, 4))
    R[:, 2] += 0.002
    p = t_test_pvalues(R)
    assert p[2] < 0.01
    assert all(0.0 <= x <= 1.0 for x in p)


def test_fail_closed():
    with pytest.raises(ValueError):
        holm([])
    with pytest.raises(ValueError):
        holm([0.5, 1.5])
    with pytest.raises(ValueError):
        holm([0.5], alpha=1.5)
    with pytest.raises(ValueError):
        t_test_pvalues(np.full((10, 2), np.nan))
