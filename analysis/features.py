"""Step 4: Feature engineering + collinearity check.

Produces the model design matrix from the analysis dataset. Prints:
  - per-feature summary (mean/std/min/max)
  - a VIF table for continuous predictors (income, employment, age shares,
    stores-per-1k, year_c). Anything >5 is flagged; nothing is dropped
    automatically -- the brief says to report and let the analyst decide.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

from config import ANALYSIS_PARQUET


CONTINUOUS_FEATURES = [
    "median_household_income",
    "emp_rate",
    "share_young_21_34",
    "share_older_55_plus",   # share_prime_35_54 dropped to avoid a "shares sum to 1" identity
    "stores_per_1k_21plus",
    "year_c",
]

MONTH_DUMMIES = [f"month_{m}" for m in range(2, 13)]  # month_1 baseline

MODEL_SPECS = {
    "minimal": {
        "features": ["median_household_income"] + MONTH_DUMMIES,
        "note": "Income + month indicators (baseline).",
    },
    "income_year": {
        "features": ["median_household_income", "year_c"] + MONTH_DUMMIES,
        "note": "Income + year trend + months.",
    },
    "econ": {
        "features": ["median_household_income", "emp_rate", "year_c"] + MONTH_DUMMIES,
        "note": "Income + employment + year + months.",
    },
    "econ_age": {
        "features": ["median_household_income", "emp_rate",
                     "share_young_21_34", "share_older_55_plus",
                     "year_c"] + MONTH_DUMMIES,
        "note": "Adds age structure (share_prime_35_54 = baseline).",
    },
    "full": {
        "features": CONTINUOUS_FEATURES + MONTH_DUMMIES,
        "note": "All continuous features + months.",
    },
}


def load_analysis_frame() -> pd.DataFrame:
    return pd.read_parquet(ANALYSIS_PARQUET)


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Employment-to-population ratio for 16+. B23001 gives Employed only
    # within the civilian labor force; the denominator here is the full 16+
    # population, so this is an EPOP rather than the unemployment rate.
    df["emp_rate"] = df["employed_count"] / df["pop_16_plus"]

    # Age shares of the approx-21+ adult population.
    # young: 22-34 (plus half of 20-21 to be consistent with the 21+ denom)
    # prime: 35-54  (baseline; only two other shares enter the model)
    # older: 55+
    young = df[["pop_22_24", "pop_25_29", "pop_30_34"]].sum(axis=1) + 0.5 * df["pop_20_21"]
    prime = df[["pop_35_44", "pop_45_54"]].sum(axis=1)
    older = df[["pop_55_59", "pop_60_61", "pop_62_64",
                "pop_65_69", "pop_70_74", "pop_75_plus"]].sum(axis=1)
    df["share_young_21_34"] = young / df["pop_21_plus_approx"]
    df["share_prime_35_54"] = prime / df["pop_21_plus_approx"]
    df["share_older_55_plus"] = older / df["pop_21_plus_approx"]

    df["stores_per_1k_21plus"] = 1000.0 * df["n_stores"] / df["pop_21_plus_approx"]

    # Numeric year trend, centered at 2024 for interpretability
    df["year_c"] = df["year"] - 2024

    for m in range(2, 13):
        df[f"month_{m}"] = (df["month"] == m).astype(int)

    df["log_liters_per_21plus"] = np.log(df["liters_per_21plus"])
    return df


def print_feature_summary(df: pd.DataFrame) -> None:
    print("\n=== feature summary (continuous) ===")
    summ = df[CONTINUOUS_FEATURES].describe().T[["mean", "std", "min", "50%", "max"]]
    print(summ.to_string())
    print(f"\nrows: {len(df):,}   counties: {df['county_fips'].nunique()}   "
          f"years: {sorted(df['year'].unique())}")


def print_vif(df: pd.DataFrame, features=None, subset: str = "training") -> pd.DataFrame:
    features = features or CONTINUOUS_FEATURES
    d = df[df["year"] <= 2025] if subset == "training" else df
    X = add_constant(d[features].dropna())
    rows = []
    for i, name in enumerate(X.columns):
        if name == "const":
            continue
        vif = variance_inflation_factor(X.values, i)
        rows.append({"feature": name, "VIF": round(vif, 3),
                     "flag": "*HIGH*" if vif > 5 else ""})
    tbl = pd.DataFrame(rows).sort_values("VIF", ascending=False)
    print(f"\n=== VIF ({subset} rows, {len(d):,}) ===")
    print(tbl.to_string(index=False))
    return tbl


if __name__ == "__main__":
    raw = load_analysis_frame()
    df = build_feature_frame(raw)
    print_feature_summary(df)
    print_vif(df, CONTINUOUS_FEATURES, subset="training")
