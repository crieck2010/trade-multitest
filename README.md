> [!IMPORTANT]
> **Consolidated into [TradeSuite](https://github.com/crieck2010/trade-suite)**  
> This engine has been consolidated into the unified [TradeSuite monorepo](https://github.com/crieck2010/trade-suite). Active development, bug fixes, releases, and unified testing now live in `trade-suite`. This repository is preserved as an archive.

# trade-multitest

Multiple-testing correction for trading research — the canonical
multiplicity engine for the trade-suite research lane. When a research
round screens dozens of ideas and one looks good, these are the tools
that answer *"good, or good-by-luck?"*

Four corrections, one honest rule:

| Method | What it answers |
|---|---|
| **Deflated Sharpe Ratio** (Bailey & López de Prado, 2014) | P(true Sharpe > 0) for the selected trial, deflated for K trials |
| **White's Reality Check** (2000) | Does *any* screened trial genuinely beat the benchmark? |
| **Hansen's SPA** (2005) | Same question, studentised — better power, discards poor trials |
| **Holm step-down** (1979) | Conservative per-trial baseline, no dependence assumptions |

**The honesty rule.** Every method takes *all screened trials* —
`n_trials` is the number of ideas run in the research phase, not the
number reported. Passing a subset silently deflates the correction and
is the exact failure mode this package exists to prevent. This matches
the `n_trials` semantics in trade-strategies `docs/validation/GATES.md`.

Part of the [trade-suite](https://github.com/crieck2010/trade-suite) project.
Declared the canonical multiplicity engine by trade-strategies v0.4.0.

## Installation

```bash
pip install trade-multitest
```

Dependencies: Python ≥ 3.10, NumPy only. Pure engine — no UI imports,
importable and testable standalone.

## Quickstart

```python
from trade_multitest import dsr, reality_check, spa_test, holm

# Every Sharpe screened in the research phase — all of them.
trial_sharpes = [1.38, 0.87, -0.21, 0.77, 0.09, ...]  # K = len(...)

p = dsr(sr_hat=1.38, trial_sharpes=trial_sharpes, n_obs=1500,
        skew=0.2, kurt=3.5)
print(f"DSR = {p:.3f}")   # P(true Sharpe > 0) after selection bias

# Round-level: does anything beat the benchmark?
rc = reality_check(returns_2d, benchmark_returns, seed=0)
print(rc["p_value"], rc["verdict"])   # validated / invalidated
```

## CLI

```bash
trade-multitest examples/round_example.json
trade-multitest round.json --json   # machine-readable multitest.report.v1
```

Reads a JSON (or CSV) research round and prints per-trial DSR and Holm
verdicts plus the round-level Reality Check / SPA verdicts. JSON and
CSV schemas are documented in `docs/INTEROP.md`.

## Docs

- `docs/METHODOLOGY.md` — the actual maths, with paper references and
  stated simplifications.
- `docs/INTEROP.md` — `multitest.request.v1` / `multitest.report.v1`
  JSON interchange for trade-agents (Occam's Desk) and other callers.

## Language standard

Verdicts are **validated** / **invalidated** (a failed round is
**discarded** as evidence) — in code, docs, and comments.

## License

MIT — see `LICENSE`.
