# Interop

Versioned JSON interchange between `trade-multitest` and its callers —
primarily trade-agents (Occam's Desk), which will invoke the
multiplicity engine during research rounds. Schemas are versioned;
`v1` is frozen as of trade-multitest 0.1.0.

## multitest.request.v1

What a caller sends (the CLI's JSON input is exactly this schema):

```json
{
  "periods_per_year": 252,
  "alpha": 0.05,
  "seed": 0,
  "n_boot": 1000,
  "n_obs": 1500,
  "benchmark_returns": [0.001, -0.0004, "..."],
  "trials": [
    {
      "name": "idea-a",
      "sharpe": 1.20,
      "skew": 0.10,
      "kurt": 3.20,
      "n_obs": 1500,
      "returns": [0.002, -0.001, "..."]
    }
  ]
}
```

Field notes:

- `trials[].sharpe` — annualised Sharpe of the trial. **Every screened
  trial must be present** (the honesty rule); `n_trials` is derived,
  never declared separately.
- `trials[].returns` — optional per-period return series. Required for
  the Reality Check, SPA and Holm-on-t-tests; without them only the DSR
  is computed (CSV input covers this case).
- `skew` / `kurt` default to 0.0 / 3.0 (Normal) when omitted.
- `n_obs` may be given once at top level or per trial.

## multitest.report.v1

What the engine returns (`trade-multitest round.json --json`):

```json
{
  "schema": "multitest.report.v1",
  "n_trials": 77,
  "alpha": 0.05,
  "periods_per_year": 252,
  "per_trial": [
    {
      "name": "idea-a",
      "sharpe": 1.20,
      "dsr": 0.93,
      "dsr_verdict": "validated",
      "t_pvalue": 0.0012,
      "holm_p_adjusted": 0.041,
      "holm_verdict": "validated"
    }
  ],
  "round_tests": {
    "holm": {"n_rejected": 2, "n_trials": 77, "alpha": 0.05, "...": "..."},
    "reality_check": {"p_value": 0.013, "verdict": "validated", "...": "..."},
    "spa": {"p_value": 0.021, "verdict": "validated", "...": "..."}
  }
}
```

Verdict vocabulary: `"validated"` / `"invalidated"` only.

## Intended Occam's Desk wiring (trade-agents)

1. After a research round's trials are screened, the Desk assembles a
   `multitest.request.v1` with **all** screened trials (honesty rule)
   and calls `trade_multitest.cli.evaluate_round` (in-process) or the
   `trade-multitest` CLI (subprocess, `--json`).
2. The Desk's razor round consumes `per_trial[].dsr` as the
   multiplicity-adjusted skill score and `round_tests` as the
   round-level gate: a round whose Reality Check *and* SPA both read
   `"invalidated"` contributes no candidates, however good the best
   raw Sharpe looked.
3. DSR threshold semantics stay with the caller (trade-strategies
   Tier-1 uses DSR > 0.8); this engine reports the probability, not
   the policy.

## Compatibility promise

- `v1` schemas are append-only: new optional fields may be added, but
  existing fields keep their meaning. A breaking change ships as `v2`.
- All engine functions accept and return plain Python/NumPy data —
  no file handles, no network, no global state — so agents can call
  them in-process deterministically (pass `seed`).
