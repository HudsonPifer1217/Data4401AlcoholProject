library(tidyverse)
library(lubridate)
library(arrow)

liquor_data <- read_parquet("C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_datasets/iowa_liquor_sales_clean.parquet")
Iowa_weather_data = read.csv("C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_weather_dataset.csv")


#Aggregate
weekly_sales <- liquor_data |>
  mutate(
    ordered_on = as.Date(ordered_on),
    year = year(ordered_on),
    week = isoweek(ordered_on)
  ) |>
  group_by(
    year,
    week,
    category_name
  ) |>
  summarise(
    total_liters = sum(sales_liters, na.rm = TRUE),
    .groups = "drop"
  )

weather_weekly <- Iowa_weather_data |>
  mutate(
    year = 2025
  )

#Joining weather and sales
sales_weather <- weekly_sales |>
  inner_join(
    weather_weekly,
    by = c("year", "week")
  )

#Correlation
temp_correlation <- sales_weather |>
  group_by(category_name) |>
  summarise(
    correlation = cor(
      overall_temp,
      total_liters,
      use = "complete.obs"
    ),
    .groups = "drop"
  ) |>
  arrange(correlation)

temp_correlation |>
  filter(!is.na(correlation)) |>
  slice_max(
    order_by = abs(correlation),
    n = 15
  )

sales_weather_share <- sales_weather |>
  group_by(year, week) |>
  mutate(
    total_all_alcohol = sum(total_liters, na.rm = TRUE),
    sales_share = total_liters / total_all_alcohol
  ) |>
  ungroup()

share_correlation <- sales_weather_share |>
  group_by(category_name) |>
  summarise(
    correlation = cor(
      overall_temp,
      sales_share,
      use = "complete.obs"
    ),
    .groups = "drop"
  ) |>
  arrange(correlation)

share_correlation |>
  filter(!is.na(correlation)) |>
  slice_max(
    order_by = abs(correlation),
    n = 15
  )

share_correlation <- share_correlation |>
  mutate(
    category_label = case_when(
      category_name == "100% AGAVE TEQUILA" ~ "Agave Tequila",
      category_name == "FLAVORED RUM" ~ "Flavored Rum",
      category_name == "IMPORTED DISTILLED SPIRIT SPECIALTY" ~ "Imported Specialty Spirits",
      category_name == "AMERICAN FLAVORED VODKA" ~ "Flavored Vodka",
      category_name == "IMPORTED DRY GINS" ~ "Imported Gin",
      category_name == "NEUTRAL GRAIN SPIRITS FLAVORED" ~ "Flavored Grain Spirits",
      category_name == "AMERICAN SCHNAPPS" ~ "Schnapps",
      category_name == "STRAIGHT RYE WHISKIES" ~ "Rye Whiskey",
      category_name == "CANADIAN WHISKIES" ~ "Canadian Whiskey",
      category_name == "IRISH WHISKIES" ~ "Irish Whiskey",
      category_name == "AMERICAN CORDIALS & LIQUEUR" ~ "Cordials & Liqueurs",
      category_name == "AMERICAN SLOE GINS" ~ "Sloe Gin",
      category_name == "AMERICAN BRANDIES" ~ "Brandy",
      category_name == "COFFEE LIQUEURS" ~ "Coffee Liqueur",
      category_name == "CREAM LIQUEURS" ~ "Cream Liqueur",
      TRUE ~ category_name
    )
  )


share_correlation |>
  filter(!is.na(correlation)) |>
  slice_max(
    order_by = abs(correlation),
    n = 15
  ) |>
  ggplot(
    aes(
      x = reorder(category_label, correlation),
      y = correlation
    )
  ) +
  geom_col() +
  coord_flip() +
  labs(
    title = "Relationship Between Weekly Temperature and Alcohol Preference",
    subtitle = "Positive = warmer-weather preference; negative = colder-weather preference",
    x = NULL,
    y = "Correlation with Weekly Temperature"
  ) +
  theme_minimal()


#R-Squared
model <- lm(sales_share ~ overall_temp, data = sales_weather_share)

summary(model)

r_squared_results <- sales_weather_share |>
  group_by(category_name) |>
  summarise(
    r_squared = summary(
      lm(sales_share ~ overall_temp)
    )$r.squared,
    .groups = "drop"
  ) |>
  arrange(desc(r_squared))

temp_results <- sales_weather_share |>
  group_by(category_name) |>
  summarise(
    correlation = cor(
      overall_temp,
      sales_share,
      use = "complete.obs"
    ),
    
    r_squared = summary(
      lm(sales_share ~ overall_temp)
    )$r.squared,
    
    .groups = "drop"
  ) |>
  arrange(desc(r_squared))


# Weekly temperature was associated with shifts in the relative sales of several 
# alcohol categories, but low R² values indicate that temperature alone explains 
# only a small portion of purchasing variation. This suggests that temperature 
# may be useful as a seasonal stocking signal rather than as a standalone 
# predictor.