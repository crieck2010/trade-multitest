# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0).

## [0.1.0] - 2026-10-07

### Added
- `trade_multitest.dsr`: Deflated Sharpe Ratio (Bailey & López de Prado,
  2014) — `dsr()`, `dsr_from_returns()`, `expected_sharpe_null()` and the
  `moments()` helper. `n_trials` is derived from the full screened trial
  set (the GATES.md honesty rule); invalid inputs fail closed.
- `trade_multitest.reality_check`: White's Reality Check (2000) via the
  stationary bootstrap (Politis & Romano, 1994) — round-level
  validated/invalidated verdict on whether any trial beats the benchmark.
- `trade_multitest.spa`: Hansen's SPA test (2005) — studentised statistic,
  Hansen recentering, Newey-West long-run variance.
- `trade_multitest.holm`: Holm step-down (1979) plus `t_test_pvalues()`
  as the conservative per-trial baseline.
- `trade-multitest` CLI: reads a JSON/CSV research round, prints
  per-trial DSR and Holm verdicts and round-level Reality Check / SPA
  verdicts; `--json` emits the `multitest.report.v1` interchange.
- `docs/METHODOLOGY.md`: the maths with paper references and stated
  simplifications/limitations. `docs/INTEROP.md`: versioned JSON
  interchange for trade-agents (Occam's Desk).
- `examples/`: `round_example.json` + `quickstart.py`.
- Pytest suite: unit, property-style (DSR monotonic in n_trials,
  DSR = 0.5 at the null expectation, bootstrap p-value uniformity under
  the null, Holm family-wise error control) and CLI end-to-end tests.
