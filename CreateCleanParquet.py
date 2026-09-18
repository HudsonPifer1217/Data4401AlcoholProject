"""Build one clean Parquet file from the Iowa liquor sales CSVs.

Reads every iowa_liquor_sales_*.csv in Data/, drops duplicate rows, and writes
Data/iowa_liquor_sales_clean.parquet.

Why deduplicate: some of the source CSVs overlap. For example,
iowa_liquor_sales_2022_1259_rows_part_0005.csv is entirely a copy of rows already
in part_0004, which roughly doubled 2022 Q4 sales. About 1.5M of the 13.4M rows are
duplicates (2022 Q4, 2025 Q3-Q4 and 2026 Q3).

Setup:
    pip install duckdb
    Put the CSVs in Data/ (they are too large for git, so share them separately).

Run from anywhere:
    python CreateCleanParquet.py
"""

from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "Data"
CSV_PATTERN = "iowa_liquor_sales_*.csv"
OUTPUT_PATH = DATA_DIR / "iowa_liquor_sales_clean.parquet"


def main():
    csv_files = sorted(DATA_DIR.glob(CSV_PATTERN))
    if not csv_files:
        raise SystemExit(f"No {CSV_PATTERN} files found in {DATA_DIR}")
    print(f"Reading {len(csv_files)} CSV files from {DATA_DIR}")

    con = duckdb.connect()

    # sample_size=-1 scans every row when typing columns, so sparse columns such as
    # state_bottle_cost are not mistyped from the first few rows.
    source = f"""
        read_csv(
            '{DATA_DIR / CSV_PATTERN}',
            header = true,
            sample_size = -1,
            union_by_name = true
        )
    """

    rows_read = con.execute(f"SELECT count(*) FROM {source}").fetchone()[0]

    # A duplicate is a row identical in every column. invoice_id alone can't be used:
    # from late 2025 on, one ID is shared by every line item on an invoice.
    # Sorting by date keeps the output deterministic and lets date filters skip
    # whole row groups.
    rows_written = con.execute(
        f"""
        COPY (
            SELECT DISTINCT *
            FROM {source}
            ORDER BY ordered_on, invoice_id, item_no
        )
        TO '{OUTPUT_PATH}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    ).fetchone()[0]

    first, last = con.execute(
        f"SELECT min(ordered_on), max(ordered_on) FROM read_parquet('{OUTPUT_PATH}')"
    ).fetchone()
    size_mb = OUTPUT_PATH.stat().st_size / 1024**2

    print(f"Rows read:          {rows_read:,}")
    print(f"Duplicates removed: {rows_read - rows_written:,}")
    print(f"Rows written:       {rows_written:,}  ({first} to {last})")
    print(f"Wrote {OUTPUT_PATH} ({size_mb:,.1f} MiB)")

    con.close()


if __name__ == "__main__":
    main()
