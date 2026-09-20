"""Shared paths, constants, and small helpers for the analysis pipeline."""
from pathlib import Path
import glob

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

SEED = 4401

# Input files
SALES_PARQUET = DATA / "iowa_liquor_sales_clean.parquet"
INCOME_CSV = DATA / "iowa_median_household_income_in_the_past_12_months_acs_5_year_estimates_530_rows.csv"
POP16_GLOB = str(DATA / "iowa_population_16_years_and_over_by_sex_age_and_employment_status_acs_5_year_estimates_*_part_*.csv")


def pop16_parts():
    return sorted(glob.glob(POP16_GLOB))


TRAIN_YEARS = (2022, 2023, 2024, 2025)
TEST_YEARS = (2026,)

# ACS 5-year windows available in the two ACS files: 2008-2012 .. 2020-2024
LATEST_ACS_END = 2024


def acs_period_for_year(year: int) -> str:
    """Map a sales calendar year to an ACS 5-year window by end-year.

    2022 sales -> "2018-2022"; 2025 and 2026 fall back to "2020-2024"
    since ACS 2021-2025 is not yet released.
    """
    end = year if year <= LATEST_ACS_END else LATEST_ACS_END
    return f"{end - 4}-{end}"


CACHE_DIR = ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)
COUNTY_MONTH_PARQUET = CACHE_DIR / "county_month.parquet"
EXTERNALS_PARQUET = CACHE_DIR / "externals_by_county_year.parquet"
ANALYSIS_PARQUET = CACHE_DIR / "analysis_dataset.parquet"
