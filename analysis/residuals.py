"""Step 8 + Step 10: residual analysis and the four required plots.

Refits the selected model on ALL training data (2022-2025), computes residuals
per county-month, aggregates residuals to the county level, standardizes,
flags |z| > 2, and writes plots + tables to output/.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

from config import ANALYSIS_PARQUET, OUT
from features import build_feature_frame, MODEL_SPECS
from model_cv import fit_wls, training_slice


SELECTED_SPEC = "full"


def _style():
    plt.rcParams.update({
        "figure.figsize": (7.5, 5.0),
        "figure.dpi": 120,
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "savefig.bbox": "tight",
    })


def refit_and_score(df: pd.DataFrame, spec_name: str = SELECTED_SPEC):
    train = training_slice(df)
    feats = MODEL_SPECS[spec_name]["features"]
    model = fit_wls(train, feats)

    X = sm.add_constant(train[feats].astype(float), has_constant="add")
    X = X.reindex(columns=model.params.index, fill_value=0.0)
    y_log = train["log_liters_per_21plus"].values
    yhat_log = model.predict(X).values
    resid_log = y_log - yhat_log

    train = train.copy()
    train["fitted_log"] = yhat_log
    train["resid_log"] = resid_log
    train["fitted_liters"] = np.exp(yhat_log)
    return model, train


def county_level_residuals(train: pd.DataFrame) -> pd.DataFrame:
    g = (train.groupby(["county_fips", "county_name"], as_index=False)
              .agg(mean_resid_log=("resid_log", "mean"),
                   mean_observed=("liters_per_21plus", "mean"),
                   mean_predicted=("fitted_liters", "mean"),
                   n_months=("resid_log", "size"),
                   pop_21plus=("pop_21_plus_approx", "mean")))
    mu = g["mean_resid_log"].mean()
    sd = g["mean_resid_log"].std(ddof=1)
    g["z_score"] = (g["mean_resid_log"] - mu) / sd
    g["flag"] = np.where(g["z_score"].abs() > 2.0,
                         np.where(g["z_score"] > 0, "HIGH", "LOW"), "")
    return g.sort_values("z_score")


def plot_resid_vs_fitted(train: pd.DataFrame) -> Path:
    fig, ax = plt.subplots()
    ax.scatter(train["fitted_log"], train["resid_log"], s=4, alpha=0.25)
    ax.axhline(0, color="black", lw=1)
    ax.set_xlabel("Fitted log(liters per 21+ adult)")
    ax.set_ylabel("Residual (log units)")
    ax.set_title("Residuals vs. fitted values (WLS, log target)")
    out = OUT / "residuals_vs_fitted.png"
    fig.savefig(out); plt.close(fig)
    return out


def plot_qq(train: pd.DataFrame) -> Path:
    fig, ax = plt.subplots()
    sm.qqplot(train["resid_log"].values, line="45", fit=True, ax=ax, markersize=3)
    ax.set_title("Q-Q plot of residuals (log target)")
    ax.set_xlabel("Theoretical quantiles (Normal)")
    ax.set_ylabel("Standardized residuals")
    out = OUT / "qq_plot.png"
    fig.savefig(out); plt.close(fig)
    return out


def plot_county_rank(county: pd.DataFrame) -> Path:
    d = county.sort_values("z_score").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = np.where(d["z_score"].abs() > 2, "#c0392b", "#7f8c8d")
    ax.scatter(range(len(d)), d["z_score"], c=colors, s=12)
    ax.axhline(0, color="black", lw=0.7)
    ax.axhline(2, color="#c0392b", ls="--", lw=0.8)
    ax.axhline(-2, color="#c0392b", ls="--", lw=0.8)
    for i, r in d.iterrows():
        if abs(r["z_score"]) > 2:
            ax.annotate(str(r["county_name"]).title(),
                        xy=(i, r["z_score"]),
                        xytext=(3, 3), textcoords="offset points", fontsize=7)
    ax.set_xlabel("Counties, ranked by mean residual")
    ax.set_ylabel("Standardized county-level residual (log units)")
    ax.set_title("County residuals ranked — thresholds at ±2 SD")
    out = OUT / "county_residual_rank.png"
    fig.savefig(out); plt.close(fig)
    return out


def plot_income_vs_percapita(train: pd.DataFrame) -> Path:
    x = train["median_household_income"].values
    y_log = train["log_liters_per_21plus"].values
    Xd = sm.add_constant(x)
    line_model = sm.OLS(y_log, Xd).fit()
    xs = np.linspace(x.min(), x.max(), 100)
    ys = np.exp(line_model.predict(sm.add_constant(xs)))
    fig, ax = plt.subplots()
    ax.scatter(x, np.exp(y_log), s=4, alpha=0.25)
    ax.plot(xs, ys, color="#c0392b", lw=1.4, label="Marginal fit (log-linear in income)")
    ax.set_xlabel("Median household income (USD)")
    ax.set_ylabel("Liters sold per 21+ adult per month")
    ax.set_title("Per-capita alcohol volume vs. median income")
    ax.legend()
    out = OUT / "income_vs_percapita.png"
    fig.savefig(out); plt.close(fig)
    return out


def main():
    _style()
    df = build_feature_frame(pd.read_parquet(ANALYSIS_PARQUET))
    model, train = refit_and_score(df, SELECTED_SPEC)
    print(f"[residuals] fitted spec={SELECTED_SPEC}  n={len(train):,}  "
          f"R²={model.rsquared:.3f}  adj-R²={model.rsquared_adj:.3f}")

    from scipy.stats import shapiro, skew, kurtosis, jarque_bera
    resid = train["resid_log"].values
    n = min(len(resid), 5000)
    sw = shapiro(resid[:n])
    jb = jarque_bera(resid)
    print(f"[residuals] skew={skew(resid):.3f}  excess_kurt={kurtosis(resid):.3f}  "
          f"Shapiro-Wilk W={sw.statistic:.3f} p={sw.pvalue:.2e} (first {n})  "
          f"Jarque-Bera stat={jb[0]:.1f} p={jb[1]:.2e}")

    county = county_level_residuals(train)
    county.to_csv(OUT / "county_residuals.csv", index=False)
    flagged = county[county["z_score"].abs() > 2].copy()
    flagged.to_csv(OUT / "flagged_counties.csv", index=False)
    print(f"\n=== flagged counties (|z|>2), n={len(flagged)} ===")
    print(flagged[["county_fips", "county_name", "mean_observed",
                   "mean_predicted", "mean_resid_log", "z_score", "flag"]]
                   .round(4).to_string(index=False))

    print(f"[plot] {plot_resid_vs_fitted(train)}")
    print(f"[plot] {plot_qq(train)}")
    print(f"[plot] {plot_county_rank(county)}")
    print(f"[plot] {plot_income_vs_percapita(train)}")


if __name__ == "__main__":
    main()
