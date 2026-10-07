# Methodology

The mathematics behind `trade-multitest`, with paper references. This
document states exactly what is implemented, including simplifications —
a multiplicity correction you cannot audit is not a correction.

## 1. Deflated Sharpe Ratio

**Paper.** Bailey, D.H. & López de Prado, M. (2014). "The Deflated
Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and
Non-Normality." *Journal of Portfolio Management* 40(5).

**Idea.** You run K trials and report the best Sharpe, SR̂. Under the
null (all trials have true Sharpe 0), the *expected maximum* of K
Sharpe estimates is positive — selection bias. The DSR is the
probability that the true Sharpe exceeds 0 *after* accounting for that
bias:

```
DSR = Φ( (SR̂ − SR₀) / σ̂(SR̂) )
```

**Expected Sharpe under the null.** For K trials with Sharpe-ratio
sample variance V:

```
SR₀ = √V · ( (1−γ)·Φ⁻¹(1 − 1/K) + γ·Φ⁻¹(1 − 1/(K·e)) )
```

γ ≈ 0.5772 is the Euler-Mascheroni constant. For K = 1 there is no
selection and SR₀ = 0.

**Standard error (Lo, 2002).** "The Statistics of Sharpe Ratios."
*Financial Analysts Journal* 58(4). Non-normal correction using the
selected strategy's sample skewness γ₃ and kurtosis γ₄:

```
σ̂(SR̂) = √( (1 − γ₃·SR̂ + (γ₄−1)/4 · SR̂²) / T )
```

computed per-period on T observations, then annualised consistently
with SR̂.

**Honesty rule.** K = the number of *screened* ideas in the research
phase — every trial run, not the reported subset. Implemented by
deriving K from `len(trial_sharpes)`; callers pass the full set.

## 2. White's Reality Check

**Paper.** White, H. (2000). "A Reality Check for Data Snooping."
*Econometrica* 68(5).

**Idea.** Let f_{k,t} = r_{k,t} − r_{0,t} be trial k's excess return over
the benchmark. Null: max_k E[f_k] ≤ 0 (nothing beats the benchmark).
Test statistic: T_n = max_k √n·f̄_k. The null distribution comes from
the stationary bootstrap, recentering each bootstrap replicate at the
observed means (i.e. imposing the least-favourable null configuration):

```
T*_b = max_k √n·(f̄*_k − f̄_k),   p = #{T*_b ≥ T_n} / (B + 1)
```

**Bootstrap.** Politis, D.N. & Romano, J.P. (1994). "The Stationary
Bootstrap." *JASA* 89(428). Blocks start at uniform positions with
geometric lengths of mean `block_len` (default ⌈n^{1/3}⌉), wrapping at
the series end — vectorised over replications.

**Verdict.** Round-level: p < α rejects the null → `"validated"` (at
least one trial genuinely beats the benchmark); otherwise
`"invalidated"`.

## 3. Hansen's SPA

**Paper.** Hansen, P.R. (2005). "A Test for Superior Predictive
Ability." *Journal of Business & Economic Statistics* 23(4).

**Improvement over Reality Check.** Three changes: (i) the statistic is
*studentised* — each trial scaled by its own long-run standard error,
so a volatile lucky trial cannot dominate; (ii) floored at zero; (iii)
poor trials are discarded from the bootstrap law via recentering, which
restores power and consistency when some trials are worthless:

```
T_SPA  = max(0, max_k √n·d̄_k/ω̂_k)
μ̂ᶜ_k   = d̄_k · 1{ √n·d̄_k/ω̂_k ≥ −√(2·log·log n) }
T*_b   = max(0, max_k √n·(d̄*_k − μ̂ᶜ_k)/ω̂_k)
```

**Long-run variance.** Newey-West (Bartlett kernel); default lag
⌊4·(n/100)^{2/9}⌋ per Newey & West (1994). Bootstrap law again via the
stationary bootstrap.

## 4. Holm step-down

**Paper.** Holm, S. (1979). "A Simple Sequentially Rejective Multiple
Test Procedure." *Scandinavian Journal of Statistics* 6(2).

Given one p-value per trial (e.g. one-sided t-tests of mean excess
return > 0): sort ascending, reject H_(i) while p_(i) ≤ α/(m−i+1),
stopping at the first failure. Controls the family-wise error rate at
α under *no* dependence assumptions, with strictly more power than
Bonferroni. The conservative baseline: if Holm rejects a trial, the
evidence is robust to the weakest assumptions in this package.

**Do not** feed DSR outputs (or 1 − DSR) into Holm — the DSR already
carries the multiplicity correction; that would double-count it. Holm
applies to *raw* per-trial p-values.

## Stated simplifications and limitations

1. **No SciPy.** The normal CDF uses the Abramowitz-Stegun erf
   approximation (~1e-7) and the inverse CDF uses Acklam's algorithm
   (~1e-9). More than adequate for p-values and quantiles here; not
   suitable for extreme-tail (p < 1e-9) work.
2. **t-test p-values use the normal approximation.** Valid
   asymptotically; the package targets backtests with n ≳ 30. For exact
   small-sample inference use the bootstrap tests.
3. **Default block length ⌈n^{1/3}⌉** is a reasonable rule of thumb,
   not the Politis-White automatic selector. Override `block_len`
   when the data's dependence structure is known.
4. **DSR assumes the trial Sharpe variance V is representative** of
   the null law — violated if the trial set mixes wildly different
   strategy families or lookbacks. The honesty rule (all screened
   trials) mitigates cherry-picking but not heterogeneity.
5. **Bootstrap tests assume stationarity** of the excess-return
   series. Regime breaks in the backtest window weaken all three
   bootstrap-based inferences — which is why the suite pairs them
   with the regime-aware validation in trade-strategies.
6. **These are statistical corrections, not oracles.** A validated
   round can still fail live (costs, capacity, regime change). A
   multiplicity correction removes one specific lie — "the best of K
   looked good by construction" — and no other.
