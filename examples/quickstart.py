"""Quickstart: multiplicity-adjusted verdicts for a research round.

Run:  python examples/quickstart.py
CLI:  trade-multitest examples/round_example.json
"""

import numpy as np

from trade_multitest import dsr, holm, reality_check, spa_test, t_test_pvalues

rng = np.random.default_rng(7)
n = 1500

# Six screened trials: five noise, one genuine edge (the honesty rule —
# every screened trial is passed, not just the good-looking ones).
trials = {
    "idea-a": rng.normal(0.0, 0.01, n),
    "idea-b": rng.normal(-0.002, 0.01, n),
    "idea-c": rng.normal(0.0, 0.01, n),
    "idea-d": rng.normal(0.0, 0.01, n),
    "idea-e": rng.normal(0.0, 0.01, n),
    "idea-f": rng.normal(0.0011, 0.01, n),
}
names = list(trials.keys())
R = np.column_stack([trials[k] for k in names])
sharpes = [(R[:, j].mean() / R[:, j].std()) * np.sqrt(252) for j in range(R.shape[1])]

print("per-trial DSR (n_trials = all 6 screened):")
for name, sr in zip(names, sharpes):
    p = dsr(sr, sharpes, n)
    print(f"  {name:16s} sharpe={sr:+.3f}  DSR={p:.3f} "
          f"[{'validated' if p > 0.8 else 'invalidated'}]")

print("\nround-level bootstrap tests:")
rc = reality_check(R, n_boot=500, seed=7)
print(f"  White Reality Check: p={rc['p_value']:.4f} [{rc['verdict']}]")
sp = spa_test(R, n_boot=500, seed=7)
print(f"  Hansen SPA:          p={sp['p_value']:.4f} [{sp['verdict']}]")

print("\nHolm on raw t-test p-values:")
h = holm(t_test_pvalues(R))
for name, rej in zip(names, h["reject"]):
    print(f"  {name:16s} [{'validated' if rej else 'invalidated'}]")
