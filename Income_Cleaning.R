library(tidyverse)
income_data <- read.csv("C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/IOWA_M~1/IOWA_M~1.csv") #change file path

income_clean <- income_data |>
  filter(geography_type == "County") |>
  select(geography_name, data_collection_period, is_current_period, median_household_income, margin_of_error, change, change_rate)




find <- income_clean |>
  distinct(geography_name) #double checking all counties exist
  
