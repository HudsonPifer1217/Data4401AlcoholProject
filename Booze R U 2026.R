library(tidyverse)

sales_2026_1 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2026_1263_rows/iowa_liquor_sales_2026_1263_rows_part_0001.csv"
)

sales_2026_2 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2026_1263_rows/iowa_liquor_sales_2026_1263_rows_part_0002.csv"
)

sales_2026_3 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2026_1263_rows/iowa_liquor_sales_2026_1263_rows_part_0003.csv"
)

sales_2026_4 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2026_1263_rows/iowa_liquor_sales_2026_1263_rows_part_0004.csv"
)

sales_2026 <- rbind(
  sales_2026_1,
  sales_2026_2,
  sales_2026_3,
  sales_2026_4
)

# Formatting date (ordered_by)
all_sales <- sales_2026 %>%
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
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_monthly_totals_2026.csv",
  row.names = FALSE
)
