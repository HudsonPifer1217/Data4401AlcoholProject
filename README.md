# Data4401 — Iowa Liquor Sales Regression Analysis

Interpretable linear-regression analysis of Iowa county-level alcohol
purchasing. Estimates which county characteristics (income, employment,
age structure, retail density) are associated with higher or lower
per-adult liter volume, and flags counties that buy substantially more
or less than their characteristics would predict.

The brief is explanatory, not predictive: coefficient interpretability
and sign stability across cross-validation folds are weighted more
heavily than raw held-out error.

## Layout

```
analysis/
  config.py            paths, seeds, ACS-window mapping
  build_dataset.py     load + clean + aggregate to county-month; join externals
  features.py          feature engineering, summary + VIF
  model_cv.py          WLS fit, hand-rolled 5-fold county-grouped CV, model selection
  residuals.py         refit selected spec, county-level residuals + Q-Q + plots
  holdout.py           evaluate on 2026 (Jan-Aug)
cache/                 intermediate parquets (git-ignored)
output/                CSV tables + PNG plots (git-ignored)
Data/                  raw inputs (git-ignored, do not commit)
```

## How to run

Uses the Anaconda Python at `/opt/anaconda3/bin/python` (pandas 2.2.2,
statsmodels 0.15, numpy, scipy, matplotlib, pyarrow, scikit-learn - only
`sklearn.metrics` is imported from sklearn; the brief forbids
`sklearn.model_selection`).

```bash
/opt/anaconda3/bin/python analysis/build_dataset.py
/opt/anaconda3/bin/python analysis/features.py
/opt/anaconda3/bin/python analysis/model_cv.py
/opt/anaconda3/bin/python analysis/residuals.py
/opt/anaconda3/bin/python analysis/holdout.py
```

Random seed is 4401 (`analysis/config.SEED`) and every step is
deterministic.

## Data sources

All inputs sit in `Data/` (git-ignored) and are read from paths defined
in `analysis/config.py`:

| File | Content | Notes |
|---|---|---|
| `iowa_liquor_sales_clean.parquet` | Transaction-level Iowa liquor sales | 11.89 M rows, 2022-01-02 -> 2026-08-31. Already de-duplicated: the raw 2022 `part_0005.csv` overlapped `part_0004.csv` (~593 k rows), and that overlap was removed before this parquet was produced. |
| `iowa_median_household_income_...530_rows.csv` | ACS 5-year rolling median household income | Actual row count 25,582 (despite the filename). Filtered to `geography_type == "County"` (1,287 rows: 99 counties x 13 windows 2008-2012 ... 2020-2024). |
| `iowa_population_16_years_and_over_..._part_000{1..7}.csv` | ACS B23001 - sex x age x labor-force x employment for pop 16+ | 7 CSV parts, ~4.4 M rows combined; filtered to county (222,651 rows: 99 x 13 x 173 cells). Sum of age brackets exactly equals `B23001_001` (0 rounding). |

## Key methodological choices

**Target: liters per approx-21+ adult per county-month.** ACS B23001
lumps 20-21 year olds into a single bracket, so exact 21+ is not
derivable. We approximate 21+ = (16+) - (16-19 bracket) - 0.5*(20-21
bracket), which assumes uniform distribution within the 20-21 bin. The
alternative of using 22+ was rejected because it discards 21-year-olds
entirely.

**Log target.** Raw per-adult liters is right-skewed (skew ~ 2.46). We
fit `log(liters_per_21+)`; coefficients read as approximate proportional
effects on the linear scale.

**Weights.** WLS with weights = approx-21+ population, so small counties
(Adams: ~3 k adults) do not exert equal leverage on the coefficients as
Polk (~370 k adults).

**Income window mapping.** ACS provides overlapping 5-year windows. Each
sales calendar year is matched to the window whose end-year equals that
year (2022 sales -> `2018-2022` window). 2025 and 2026 sales fall back
to the latest available window (`2020-2024`) because `2021-2025` was
not yet released at the time of analysis.

**County keys.** Sales counties are upper-case bare names ("POLK");
income and pop tables use "Polk County, Iowa". Joins are done on
`county_fips_code` (identical 99-code sets on both sides), and county
names are kept for display only.

**Cross-validation.** Hand-rolled 5-fold group CV: counties are shuffled
with the fixed seed and partitioned into 5 groups; each fold's
validation set is one group of counties, training is the other four.
`assert` guarantees no county appears on both sides of a fold. No
`sklearn.model_selection` primitive is used anywhere.

**Model selection.** Five candidate specs, from `minimal` (income +
month dummies) to `full` (income + employment + two age-shares + stores
per 1k + year trend + months). Selection weights sign-stability across
folds and interpretability alongside CV RMSE. `full` wins on every
axis: lowest CV RMSE (0.294 liters/adult), highest adj-R^2 (0.361), and
zero sign-unstable predictors.

## Findings (produced by `residuals.py`)

7 counties flagged with |z| > 2 on their mean county-level residual:

- **HIGH (buy more than the model predicts):** Dickinson (Iowa Great
  Lakes resort area, plausibly tourism), Cerro Gordo (Mason City hub
  county), Clinton.
- **LOW (buy less than the model predicts):** Davis (large Amish
  population), Taylor, Decatur, Louisa.

Caveat on the threshold. The residual distribution is symmetric
(skew ~ -0.21) but heavy-tailed (excess kurtosis ~ 2.20; Jarque-Bera
p ~ 0). The +/-2 SD threshold is normal-based; on a heavy-tailed
distribution it flags somewhat more counties than a strict 5%
probability would predict. See `output/qq_plot.png`.

## Outputs

All in `output/`:

- `coefficient_table_full.csv` - estimate / SE / 95 % CI / p-value for
  the full-spec fit.
- `model_selection.csv` - the 5-spec comparison table.
- `cv_folds_full.csv`, `cv_coefs_full.csv`, `cv_stability_full.csv` -
  per-fold metrics, per-fold coefficient estimates, and the
  sign-stability table.
- `county_residuals.csv` - county-level mean residual + z-score for all
  99 counties.
- `flagged_counties.csv` - the |z| > 2 subset.
- `holdout_2026.csv` - 2026 predictions and residuals per county-month.
- Four plots: `residuals_vs_fitted.png`, `qq_plot.png`,
  `county_residual_rank.png`, `income_vs_percapita.png`.

## Limitations

- **21+ approximation.** See "Target" above.
- **ACS windows are rolling 5-year estimates**, so a given "year" of
  income/demographics is really an average of the surrounding 5 years.
  2025 and 2026 sales both reuse the 2020-2024 window because no newer
  ACS is available.
- **`share_older_55_plus` and `share_young_21_34` have VIF ~ 6 and 5**
  respectively (age-shares mechanically sum to 1). Coefficients on
  those two shares are interpretable relative to the omitted
  `share_prime_35_54` baseline but should not be read as fully
  independent.
- **Off-premise only.** Iowa's sales database records shipments from
  the state wholesaler to licensed retailers, so on-premise consumption
  (bars, restaurants) is not captured. This likely biases the Dickinson
  flag downward and the Davis flag reflects genuine low consumption.
- **Held-out R^2 is essentially zero.** Coefficient interpretation is
  reliable (sign-stable across folds) but the model has little
  county-level predictive power beyond seasonality and demographics -
  consistent with the explanatory framing.
