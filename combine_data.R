#!/usr/bin/env Rscript

# Combine all CSV files in a folder into one dataset.
# Usage:
#   Rscript combine_datasets.R [input_folder] [output_file]
# Example:
#   Rscript combine_datasets.R . combined_dataset.csv

args <- commandArgs(trailingOnly = TRUE)

if (!requireNamespace("data.table", quietly = TRUE)) {
  install.packages("data.table", repos = "https://cloud.r-project.org")
}

# Read from and write to R's current working directory by default.
input_folder <- if (length(args) >= 1) args[[1]] else getwd()
output_file <- if (length(args) >= 2) args[[2]] else file.path(getwd(), "combined_dataset.csv")

if (!dir.exists(input_folder)) {
  stop(sprintf("Input folder does not exist: %s", input_folder))
}

file_names <- c(
  "iowa_liquor_sales_2022_1259_rows_part_0001.csv",
  "iowa_liquor_sales_2022_1259_rows_part_0002.csv",
  "iowa_liquor_sales_2022_1259_rows_part_0003.csv",
  "iowa_liquor_sales_2022_1259_rows_part_0004.csv",
  "iowa_liquor_sales_2022_1259_rows_part_0005.csv",
  "iowa_liquor_sales_2023_1260_rows_part_0001.csv",
  "iowa_liquor_sales_2023_1260_rows_part_0002.csv",
  "iowa_liquor_sales_2023_1260_rows_part_0003.csv",
  "iowa_liquor_sales_2023_1260_rows_part_0004.csv",
  "iowa_liquor_sales_2023_1260_rows_part_0005.csv",
  "iowa_liquor_sales_2024_1261_rows_part_0001.csv",
  "iowa_liquor_sales_2024_1261_rows_part_0002.csv",
  "iowa_liquor_sales_2024_1261_rows_part_0003.csv",
  "iowa_liquor_sales_2024_1261_rows_part_0004.csv",
  "iowa_liquor_sales_2024_1261_rows_part_0005.csv",
  "iowa_liquor_sales_2025_1262_rows_part_0001.csv",
  "iowa_liquor_sales_2025_1262_rows_part_0002.csv",
  "iowa_liquor_sales_2025_1262_rows_part_0003.csv",
  "iowa_liquor_sales_2025_1262_rows_part_0004.csv",
  "iowa_liquor_sales_2025_1262_rows_part_0005.csv",
  "iowa_liquor_sales_2026_1263_rows_part_0001.csv",
  "iowa_liquor_sales_2026_1263_rows_part_0002.csv",
  "iowa_liquor_sales_2026_1263_rows_part_0003.csv",
  "iowa_liquor_sales_2026_1263_rows_part_0004.csv"
)

csv_files <- file.path(input_folder, file_names)
missing_files <- csv_files[!file.exists(csv_files)]
if (length(missing_files) > 0) {
  stop(sprintf("These expected files were not found:\n%s",
               paste(basename(missing_files), collapse = "\n")))
}

read_one <- function(path) {
  data <- data.table::fread(
    path,
    na.strings = c("", "NA", "N/A", "NULL"),
    showProgress = FALSE
  )
  data[, source_file := basename(path)]
  data
}

datasets <- lapply(csv_files, read_one)
combined_dataset <- data.table::rbindlist(datasets, use.names = TRUE, fill = TRUE)
data.table::fwrite(combined_dataset, output_file, na = "")

message(sprintf(
  "Combined %d files and %d rows into %s",
  length(csv_files), nrow(combined_dataset), normalizePath(output_file, mustWork = FALSE)
))
