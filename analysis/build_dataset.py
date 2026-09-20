"""Step 1-3: Build the county-month analysis dataset.

- Read the clean sales parquet.
- Filter to rows with a non-null county and legal-drinker-relevant columns.
- Aggregate to (county_fips, year, month): total liters, dollars, distinct stores.
- Join to income (ACS 5-yr window by end-year, fallback to latest for 2025/2026).
- Join to population/employment (same window rule): total 16+, approx 21+ adult
  population, employment count, age-bracket population shares.
- Compute target: liters per approx-21+ adult, per county-month.

The 21+ denominator is approximated as (16+) - (16-19) - 0.5*(20-21) because the
ACS B23001 table lumps 20 and 21 year olds into one bracket. Documented in the
README.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd

from config import (
    SALES_PARQUET,
    INCOME_CSV,
    pop16_parts,
    COUNTY_MONTH_PARQUET,
    EXTERNALS_PARQUET,
    ANALYSIS_PARQUET,
    acs_period_for_year,
)


def _print(msg: str) -> None:
    print(msg, flush=True)


def aggregate_sales_to_county_month() -> pd.DataFrame:
    _print(f"[sales] reading {SALES_PARQUET.name} ...")
    cols = ["ordered_on", "county_fips_code", "county_name",
            "store_no", "sales_liters", "sales_dollars"]
    df = pd.read_parquet(SALES_PARQUET, columns=cols)
    _print(f"[sales] loaded rows={len(df):,}")

    df["ordered_on"] = pd.to_datetime(df["ordered_on"], errors="coerce")
    n_before = len(df)
    df = df.dropna(subset=["ordered_on", "county_fips_code"])
    _print(f"[sales] dropped {n_before - len(df):,} rows with null date or FIPS -> {len(df):,}")

    df["year"] = df["ordered_on"].dt.year
    df["month"] = df["ordered_on"].dt.month
    df["county_fips"] = df["county_fips_code"].astype(int)

    agg = (df.groupby(["county_fips", "county_name", "year", "month"], as_index=False)
             .agg(total_liters=("sales_liters", "sum"),
                  total_dollars=("sales_dollars", "sum"),
                  n_stores=("store_no", "nunique"),
                  n_transactions=("sales_liters", "size")))
    _print(f"[sales] county-month rows: {len(agg):,}  "
           f"(unique counties={agg['county_fips'].nunique()}, "
           f"unique year-months={agg[['year','month']].drop_duplicates().shape[0]})")
    return agg


def load_income_by_county_period() -> pd.DataFrame:
    _print(f"[income] reading {INCOME_CSV.name} ...")
    inc = pd.read_csv(INCOME_CSV, low_memory=False)
    _print(f"[income] loaded rows={len(inc):,}")
    before = len(inc)
    cty = inc[inc["geography_type"].str.lower().eq("county")].copy()
    _print(f"[income] dropped {before - len(cty):,} non-county rows "
           f"(Place/Tract/State) -> {len(cty):,}")
    cty["county_fips"] = cty["county_fips_code"].astype(int)
    keep = ["county_fips", "geography_name", "data_collection_period",
            "median_household_income"]
    return cty[keep]


AGE_BRACKET_TO_COL = {
    "16 to 19 Years": "pop_16_19",
    "20 and 21 Years": "pop_20_21",
    "22 to 24 Years": "pop_22_24",
    "25 to 29 Years": "pop_25_29",
    "30 to 34 Years": "pop_30_34",
    "35 to 44 Years": "pop_35_44",
    "45 to 54 Years": "pop_45_54",
    "55 to 59 Years": "pop_55_59",
    "60 and 61 Years": "pop_60_61",
    "62 to 64 Years": "pop_62_64",
    "65 to 69 Years": "pop_65_69",
    "70 to 74 Years": "pop_70_74",
    "75 Years and Over": "pop_75_plus",
}


def load_pop16_by_county_period() -> pd.DataFrame:
    """Combine 7 pop16+ parts and derive per-county-period features."""
    parts = pop16_parts()
    _print(f"[pop16] combining {len(parts)} part(s) ...")
    frames = []
    total_rows = 0
    for p in parts:
        d = pd.read_csv(p, low_memory=False)
        total_rows += len(d)
        frames.append(d[d["geography_type"].str.lower().eq("county")])
    raw = pd.concat(frames, ignore_index=True)
    _print(f"[pop16] combined raw rows={total_rows:,}  county rows={len(raw):,}  "
           f"dropped {total_rows - len(raw):,} non-county rows")

    raw["county_fips"] = raw["county_fips_code"].astype(int)

    total = (raw[raw["variable"] == "B23001_001"]
             [["county_fips", "data_collection_period", "population"]]
             .rename(columns={"population": "pop_16_plus"}))
    _print(f"[pop16] total-16+ rows: {len(total):,}")

    # Age-bracket rows: for each sex, the bracket TOTAL cell (child cells are
    # already split by labor-force / armed-forces / employment). The bracket
    # totals are where age_range is set and is_in_labor_force is null.
    age_totals = raw[raw["age_range"].notna() & raw["is_in_labor_force"].isna()]
    age_by_county = (age_totals
                     .groupby(["county_fips", "data_collection_period", "age_range"],
                              as_index=False)["population"].sum())
    missing = set(age_by_county["age_range"].unique()) - set(AGE_BRACKET_TO_COL)
    if missing:
        raise ValueError(f"Unexpected age_range values: {missing}")
    age_by_county["age_col"] = age_by_county["age_range"].map(AGE_BRACKET_TO_COL)
    age_wide = (age_by_county
                .pivot_table(index=["county_fips", "data_collection_period"],
                             columns="age_col", values="population", aggfunc="sum")
                .reset_index())
    age_wide.columns.name = None

    emp = (raw[raw["employment_status"] == "Employed"]
           .groupby(["county_fips", "data_collection_period"], as_index=False)["population"].sum()
           .rename(columns={"population": "employed_count"}))

    out = (total
           .merge(age_wide, on=["county_fips", "data_collection_period"], how="left")
           .merge(emp,      on=["county_fips", "data_collection_period"], how="left"))

    age_cols = [c for c in AGE_BRACKET_TO_COL.values()]
    age_sum = out[age_cols].sum(axis=1)
    max_diff = (age_sum - out["pop_16_plus"]).abs().max()
    _print(f"[pop16] max |sum-of-age-brackets - pop_16_plus| = {max_diff} (rounding OK)")

    out["pop_21_plus_approx"] = (out["pop_16_plus"]
                                  - out["pop_16_19"].fillna(0)
                                  - 0.5 * out["pop_20_21"].fillna(0))
    _print(f"[pop16] rows: {len(out):,}  counties={out['county_fips'].nunique()}  "
           f"periods={out['data_collection_period'].nunique()}")
    return out


def build_externals_by_county_year(years: list[int]) -> pd.DataFrame:
    inc = load_income_by_county_period()
    pop = load_pop16_by_county_period()

    frames = []
    for y in years:
        period = acs_period_for_year(y)
        i = inc[inc["data_collection_period"] == period][
            ["county_fips", "geography_name", "median_household_income"]]
        p = pop[pop["data_collection_period"] == period].drop(columns=["data_collection_period"])
        m = i.merge(p, on="county_fips", how="inner")
        m["year"] = y
        m["acs_period"] = period
        frames.append(m)
        _print(f"[externals] year={y} period={period} rows={len(m):,}  "
               f"income_only={len(i)-len(m)}  pop_only={len(p)-len(m)}")
    return pd.concat(frames, ignore_index=True)


def build_analysis_dataset() -> pd.DataFrame:
    cm = aggregate_sales_to_county_month()
    cm.to_parquet(COUNTY_MONTH_PARQUET, index=False)
    _print(f"[cache] wrote {COUNTY_MONTH_PARQUET}")

    years = sorted(cm["year"].unique().tolist())
    ext = build_externals_by_county_year(years)
    ext.to_parquet(EXTERNALS_PARQUET, index=False)
    _print(f"[cache] wrote {EXTERNALS_PARQUET}")

    _print(f"[join] cm rows={len(cm):,}  externals rows={len(ext):,}")
    df = cm.merge(ext, on=["county_fips", "year"], how="left", suffixes=("", "_ext"))
    unmatched = df["pop_16_plus"].isna().sum()
    _print(f"[join] merged rows={len(df):,}  unmatched (no externals)={unmatched}")
    if unmatched:
        bad = df[df["pop_16_plus"].isna()][["county_fips", "county_name", "year"]].drop_duplicates()
        _print("[join] unmatched county-years (first 30):")
        _print(bad.head(30).to_string())

    df["liters_per_21plus"] = df["total_liters"] / df["pop_21_plus_approx"]
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))

    df = df.sort_values(["county_fips", "year", "month"]).reset_index(drop=True)
    df.to_parquet(ANALYSIS_PARQUET, index=False)
    _print(f"[cache] wrote {ANALYSIS_PARQUET}  final rows={len(df):,}")
    return df


if __name__ == "__main__":
    df = build_analysis_dataset()
    _print("\n=== analysis dataset head ===")
    _print(df.head(3).to_string())
    _print("\n=== target summary (liters_per_21plus) ===")
    _print(df["liters_per_21plus"].describe().to_string())
    _print(f"\nskew: {df['liters_per_21plus'].skew():.3f}")
