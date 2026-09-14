library(tidyverse)

# Read files (use your own filepaths)
# 2022
sales_2022_1 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2022_1259_rows/iowa_liquor_sales_2022_1259_rows_part_0001.csv"
)

sales_2022_2 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2022_1259_rows/iowa_liquor_sales_2022_1259_rows_part_0002.csv"
)

sales_2022_3 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2022_1259_rows/iowa_liquor_sales_2022_1259_rows_part_0003.csv"
)

sales_2022_4 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2022_1259_rows/iowa_liquor_sales_2022_1259_rows_part_0004.csv"
)

sales_2022_5 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2022_1259_rows/iowa_liquor_sales_2022_1259_rows_part_0005.csv"
)

sales_2022 <- rbind(
  sales_2022_1,
  sales_2022_2,
  sales_2022_3,
  sales_2022_4,
  sales_2022_5
)


# 2023
sales_2023_1 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2023_1260_rows/iowa_liquor_sales_2023_1260_rows_part_0001.csv"
)

sales_2023_2 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2023_1260_rows/iowa_liquor_sales_2023_1260_rows_part_0002.csv"
)

sales_2023_3 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2023_1260_rows/iowa_liquor_sales_2023_1260_rows_part_0003.csv"
)

sales_2023_4 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2023_1260_rows/iowa_liquor_sales_2023_1260_rows_part_0004.csv"
)

sales_2023_5 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2023_1260_rows/iowa_liquor_sales_2023_1260_rows_part_0005.csv"
)

sales_2023 <- rbind(
  sales_2023_1,
  sales_2023_2,
  sales_2023_3,
  sales_2023_4,
  sales_2023_5
)


# 2024
sales_2024_1 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2024_1261_rows/iowa_liquor_sales_2024_1261_rows_part_0001.csv"
)

sales_2024_2 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2024_1261_rows/iowa_liquor_sales_2024_1261_rows_part_0002.csv"
)

sales_2024_3 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2024_1261_rows/iowa_liquor_sales_2024_1261_rows_part_0003.csv"
)

sales_2024_4 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2024_1261_rows/iowa_liquor_sales_2024_1261_rows_part_0004.csv"
)

sales_2024_5 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2024_1261_rows/iowa_liquor_sales_2024_1261_rows_part_0005.csv"
)

sales_2024 <- rbind(
  sales_2024_1,
  sales_2024_2,
  sales_2024_3,
  sales_2024_4,
  sales_2024_5
)


# 2025
sales_2025_1 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2025_1262_rows/iowa_liquor_sales_2025_1262_rows_part_0001.csv"
)

sales_2025_2 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2025_1262_rows/iowa_liquor_sales_2025_1262_rows_part_0002.csv"
)

sales_2025_3 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2025_1262_rows/iowa_liquor_sales_2025_1262_rows_part_0003.csv"
)

sales_2025_4 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2025_1262_rows/iowa_liquor_sales_2025_1262_rows_part_0004.csv"
)

sales_2025_5 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2025_1262_rows/iowa_liquor_sales_2025_1262_rows_part_0005.csv"
)

sales_2025 <- rbind(
  sales_2025_1,
  sales_2025_2,
  sales_2025_3,
  sales_2025_4,
  sales_2025_5
)

# Combine all
all_sales <- rbind(
  sales_2022,
  sales_2023,
  sales_2024,
  sales_2025
)


# Formatting date (ordered_by) will take a while to run
all_sales <- all_sales %>%
  mutate(
    ordered_on = as.Date(ordered_on),
    Year = format(ordered_on, "%Y"),
    Month = format(ordered_on, "%m"),
    Year_Month = format(ordered_on, "%Y-%m")
  )

# Formatting by monthly
monthly_sales <- all_sales %>%
  group_by(
    Year,
    Month,
    Year_Month,
    county_name,
    store_no
  ) %>%
  summarise(
    store_name = first(store_name),
    Total_Bottles_Sold = sum(sales_bottles, na.rm = TRUE),
    Total_Liters_Sold = sum(sales_liters, na.rm = TRUE),
    Total_Gallons_Sold = sum(sales_gallons, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  arrange(
    Year,
    Month,
    county_name,
    store_no,
  )


# Save results (change location when saving)
write.csv(
  monthly_sales,
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_monthly_totals_by_county.csv",
  row.names = FALSE
)
