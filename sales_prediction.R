library(tidyverse)
library(lubridate)
library(arrow)

liquor_data <- read_parquet("C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_datasets/iowa_liquor_sales_clean.parquet")
sales_2026_1 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2026_1263_rows_part_0001.csv"
)

sales_2026_2 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2026_1263_rows_part_0002.csv"
)

sales_2026_3 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2026_1263_rows_part_0003.csv"
)

sales_2026_4 <- read.csv(
  "C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/iowa_liquor_sales_2026_1263_rows_part_0004.csv"
)

sales_2026 <- rbind(
  sales_2026_1,
  sales_2026_2,
  sales_2026_3,
  sales_2026_4
)

sum(duplicated(sales_2026))

#Formating 
sales_2026 <- sales_2026 |>
  mutate(
    ordered_on = as.Date(ordered_on),
    Year = format(ordered_on, "%Y"),
    Month = format(ordered_on, "%m"),
    Year_Month = format(ordered_on, "%Y-%m")
  )

monthly_sales <- liquor_data |>
  mutate(
    ordered_on = ymd(ordered_on),
    Year = year(ordered_on),
    Month = month(ordered_on),
    Year_Month = floor_date(ordered_on, "month")
  ) |>
  group_by(
    Year,
    Month,
    Year_Month
  ) |>
  summarise(
    Total_Sales_Dollars = sum(sales_dollars, na.rm = TRUE),
    .groups = "drop"
  ) |>
  arrange(Year_Month)

monthly_sales <- monthly_sales |>
  mutate(
    Time = row_number()
  )

#Linear model
sales_model <- lm(
  Total_Sales_Dollars ~ Time + factor(Month),
  data = monthly_sales
)

summary(sales_model)

#Validation Function
evaluate_period <- function(data, train_end_year, validation_year) {
  
  train_data <- data |>
    filter(Year <= train_end_year)
  validation_data <- data |>
    filter(Year == validation_year)
  
  model <- lm(
    Total_Sales_Dollars ~ Time + factor(Month),
    data = train_data
  )
  
  predictions <- predict(
    model,
    newdata = validation_data
  )
  
  actual <- validation_data$Total_Sales_Dollars
  
  rmse <- sqrt(
    mean(
      (actual - predictions)^2
    )
  )
  
  mape <- mean(
    abs(
      (actual - predictions) / actual
    )
  ) * 100
  
  
  return(
    tibble(
      Train_Through = train_end_year,
      Validation_Year = validation_year,
      RMSE = rmse,
      MAPE = mape
    )
  )
}

#Validation on model
results_2023 <- evaluate_period(
  monthly_sales,
  train_end_year = 2022,
  validation_year = 2023
)

results_2024 <- evaluate_period(
  monthly_sales,
  train_end_year = 2023,
  validation_year = 2024
)

results_2025 <- evaluate_period(
  monthly_sales,
  train_end_year = 2024,
  validation_year = 2025
)


cv_results <- bind_rows(
  results_2023,
  results_2024,
  results_2025
)

cv_results

cv_results |>
  summarise(
    Average_RMSE = mean(RMSE),
    Average_MAPE = mean(MAPE)
  )

train_2024 <- monthly_sales |>
  filter(Year <= 2024)

test_2025 <- monthly_sales |>
  filter(Year == 2025)


model_2025 <- lm(
  Total_Sales_Dollars ~ Time + factor(Month),
  data = train_2024
)


test_2025 <- test_2025 |>
  mutate(
    Predicted_Sales = predict(
      model_2025,
      newdata = test_2025
    )
  )

ggplot(test_2025, aes(x = Year_Month)) +
  geom_line(
    aes(
      y = Total_Sales_Dollars,
      color = "Actual"
    ),
    linewidth = 1
  ) +
  geom_line(
    aes(
      y = Predicted_Sales,
      color = "Predicted"
    ),
    linewidth = 1
  ) +
  labs(
    title = "2025 Alcohol Sales: Actual vs Predicted",
    subtitle = "Model trained using 2022-2024 data",
    x = "Month",
    y = "Sales ($)",
    color = NULL
  ) +
  
  scale_y_continuous(
    labels = scales::dollar
  )

final_model <- lm(
  Total_Sales_Dollars ~ Time + factor(Month),
  data = monthly_sales
)

#Final test on 2026
sales_2026 <- sales_2026 |>
  distinct()

monthly_2026 <- sales_2026 |>
  mutate(
    Year = as.numeric(Year),
    Month = as.numeric(Month),
    Year_Month = make_date(
      year = Year,
      month = Month,
      day = 1
    )
  ) |>
  group_by(
    Year,
    Month,
    Year_Month
  ) |>
  summarise(
    Total_Sales_Dollars = sum(sales_dollars, na.rm = TRUE),
    .groups = "drop"
  ) |>
  arrange(Year_Month)

monthly_2026 <- monthly_2026 |>
  mutate(
    Time = max(monthly_sales$Time) + row_number()
  )

monthly_2026 <- monthly_2026 |>
  mutate(
    Predicted_Sales = predict(
      final_model,
      newdata = monthly_2026
    )
  )

rmse_2026 <- sqrt(
  mean(
    (
      monthly_2026$Total_Sales_Dollars -
        monthly_2026$Predicted_Sales
    )^2
  )
)

mape_2026 <- mean(
  abs(
    (
      monthly_2026$Total_Sales_Dollars -
        monthly_2026$Predicted_Sales
    ) /
      monthly_2026$Total_Sales_Dollars
  )
) * 100

#Results
cat(
  "2026 Final Test RMSE: $",
  round(rmse_2026, 2),
  "\n"
)

cat(
  "2026 Final Test MAPE:",
  round(mape_2026, 2),
  "%\n"
)

monthly_2026 |>
  select(
    Year_Month,
    Total_Sales_Dollars,
    Predicted_Sales
  )

ggplot(
  monthly_2026,
  aes(x = Year_Month)
) +
  geom_line(
    aes(
      y = Total_Sales_Dollars,
      color = "Actual"
    ),
    linewidth = 1
  ) +
  geom_line(
    aes(
      y = Predicted_Sales,
      color = "Predicted"
    ),
    linewidth = 1
  ) +
  geom_point(
    aes(
      y = Total_Sales_Dollars,
      color = "Actual"
    )
  ) +
  geom_point(
    aes(
      y = Predicted_Sales,
      color = "Predicted"
    )
  ) +
  scale_y_continuous(
    labels = scales::dollar
  ) +
  labs(
    title = "2026 Iowa Alcohol Sales: Actual vs Predicted",
    subtitle = "Final model trained on 2022-2025 data",
    x = "Month",
    y = "Monthly Sales",
    color = NULL
  )

#Forecast
all_monthly_sales <- bind_rows(
  monthly_sales |>
    select(
      Year,
      Month,
      Year_Month,
      Total_Sales_Dollars
    ),
  
  monthly_2026 |>
    select(
      Year,
      Month,
      Year_Month,
      Total_Sales_Dollars
    )
) |>
  arrange(Year_Month) |>
  mutate(
    Time = row_number()
  )

forecast_model <- lm(
  Total_Sales_Dollars ~ Time + factor(Month),
  data = all_monthly_sales
)

summary(forecast_model)

forecast_2027 <- tibble(
  Year = 2027,
  Month = 1:12,
  Year_Month = seq(
    from = ymd("2027-01-01"),
    to = ymd("2027-12-01"),
    by = "month"
  )
)

forecast_2027 <- forecast_2027 |>
  mutate(
    Time = max(all_monthly_sales$Time) + row_number()
  )

forecast_2027 <- forecast_2027 |>
  mutate(
    Predicted_Sales = predict(
      forecast_model,
      newdata = forecast_2027
    )
  )


# View forecast
forecast_2027 |>
  select(
    Year_Month,
    Predicted_Sales
  )

ggplot() +
  
  # Historical actual sales
  geom_line(
    data = all_monthly_sales,
    aes(
      x = Year_Month,
      y = Total_Sales_Dollars,
      color = "Actual Sales"
    ),
    linewidth = 1
  ) +
  
  # 2027 forecast
  geom_line(
    data = forecast_2027,
    aes(
      x = Year_Month,
      y = Predicted_Sales,
      color = "2027 Forecast"
    ),
    linewidth = 1
  ) +
  geom_point(
    data = forecast_2027,
    aes(
      x = Year_Month,
      y = Predicted_Sales,
      color = "2027 Forecast"
    )
  ) +
  geom_vline(
    xintercept = as.numeric(ymd("2027-01-01")),
    linetype = "dashed"
  ) +
  
  scale_y_continuous(
    labels = scales::dollar
  ) +
  labs(
    title = "Iowa Alcohol Sales Forecast for 2027",
    subtitle = "Forecast based on monthly seasonality and long-term sales trend",
    x = "Date",
    y = "Monthly Sales",
    color = NULL
  )
