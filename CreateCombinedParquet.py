"""Combine the Iowa liquor sales CSVs in Data/ into a single Parquet file with DuckDB."""

from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "Data"
CSV_GLOB = str(DATA_DIR / "*.csv")
OUTPUT_PATH = DATA_DIR / "iowa_liquor_sales.parquet"


def main():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found in {DATA_DIR}")
    print(f"Combining {len(csv_files)} CSV files from {DATA_DIR}")

    con = duckdb.connect()

    # read_csv scans the whole file when typing columns (sample_size=-1) so that
    # sparse columns such as state_bottle_cost are not mistyped from the first rows.
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM read_csv(
                '{CSV_GLOB}',
                header = true,
                sample_size = -1,
                union_by_name = true
            )
        )
        TO '{OUTPUT_PATH}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )

    rows = con.execute(
        f"SELECT count(*) FROM read_parquet('{OUTPUT_PATH}')"
    ).fetchone()[0]
    size_mb = OUTPUT_PATH.stat().st_size / 1024**2
    print(f"Wrote {rows:,} rows to {OUTPUT_PATH} ({size_mb:,.1f} MiB)")

    con.close()


if __name__ == "__main__":
    main()
