library(tidyverse)
library(lubridate)
library(stringr)
library(geosphere)
library(dplyr)

weather_data = read.csv("C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/asos.csv")
county_coord = read.csv("C:/Users/stanl/OneDrive/Documents/OneNote Notebooks/Data Science/4401 - Data Science Process and Ethics/Project 1/Iowa_County_Coordinate.csv")

distinct_time <- weather_data |>
  distinct(valid)

#coords
str(county_coord)

county_centers <- county_coord |>
  mutate(across(everything(), str_squish)) |>
  mutate(
    North_deg = as.numeric(str_split_fixed(North, " ", 2)[,1]),
    North_min = as.numeric(str_split_fixed(North, " ", 2)[,2]),
    South_deg = as.numeric(str_split_fixed(South, " ", 2)[,1]),
    South_min = as.numeric(str_split_fixed(South, " ", 2)[,2]),
    East_deg = as.numeric(str_split_fixed(East, " ", 2)[,1]),
    East_min = as.numeric(str_split_fixed(East, " ", 2)[,2]),
    West_deg = as.numeric(str_split_fixed(West, " ", 2)[,1]),
    West_min = as.numeric(str_split_fixed(West, " ", 2)[,2])
  ) |>
  mutate(
    North_dd = North_deg + North_min / 60,
    South_dd = South_deg + South_min / 60,
    East_dd = -(East_deg + East_min / 60),
    West_dd = -(West_deg + West_min / 60)
  ) |>
  mutate(
    center_lat = (North_dd + South_dd) / 2,
    center_lon = (East_dd + West_dd) / 2
  ) |>
  select(County, center_lat, center_lon)

western_counties <- c(
  "Lyon", "Osceola", "Dickinson", "Sioux", "O'Brien", "Clay",
  "Plymouth", "Cherokee", "Buena Vista", "Woodbury", "Ida", "Sac",
  "Monona", "Crawford", "Carroll",
  "Harrison", "Shelby", "Audubon",
  "Pottawattamie", "Cass", "Adair",
  "Mills", "Montgomery", "Adams",
  "Fremont", "Page", "Taylor", "Obrien"
)

central_counties <- c(
  "Emmet", "Kossuth", "Winnebago", "Palo Alto", "Hancock",
  "Pocahontas", "Humboldt", "Wright",
  "Calhoun", "Webster", "Hamilton",
  "Greene", "Boone", "Story",
  "Guthrie", "Dallas", "Polk",
  "Madison", "Warren", "Marion",
  "Union", "Clarke", "Lucas",
  "Ringgold", "Decatur", "Wayne"
)

eastern_counties <- c(
  "Worth", "Mitchell", "Howard", "Winneshiek", "Allamakee",
  "Cerro Gordo", "Floyd", "Chickasaw", "Fayette", "Clayton",
  "Franklin", "Butler", "Bremer", "Black Hawk", "Buchanan",
  "Hardin", "Grundy", "Delaware", "Dubuque",
  "Marshall", "Tama", "Benton", "Linn", "Jones", "Jackson",
  "Jasper", "Poweshiek", "Iowa", "Johnson", "Cedar", "Clinton",
  "Mahaska", "Keokuk", "Washington", "Louisa", "Muscatine", "Scott",
  "Monroe", "Wapello", "Jefferson", "Henry", "Des Moines",
  "Appanoose", "Davis", "Van Buren", "Lee"
)

county_centers <- county_centers |>
  mutate(
    region = case_when(
      County %in% western_counties ~ "Western Iowa",
      County %in% central_counties ~ "Central Iowa",
      County %in% eastern_counties ~ "Eastern Iowa",
      TRUE ~ NA_character_
    )
  )

#Weather Stations
stations <- weather_data |>
  mutate(
    lat = as.numeric(lat),
    lon = as.numeric(lon)
  ) |>
  distinct(station, lat, lon) |>
  drop_na(lat, lon)

county_station <- county_centers |>
  crossing(
    stations |>
      rename(
        station_lat = lat,
        station_lon = lon
      )
  ) |>
  mutate(
    distance_miles = distHaversine(
      cbind(center_lon, center_lat),
      cbind(station_lon, station_lat)
    ) / 1609.344
  ) |>
  group_by(County) |>
  slice_min(
    distance_miles,
    n = 1,
    with_ties = FALSE
  ) |>
  ungroup()

#weather
str(weather_data)

weather_afternoon <- weather_data |>
  mutate(
    tmpf = as.numeric(tmpf),
    date_time = ymd_hm(valid),
    hour = hour(date_time),
    date = date(date_time),
    week = isoweek(date),
    quarter = quarter(date)
  ) |>
  filter(hour >= 14 & hour <= 18) |>
  group_by(
    station,
    date,
    week,
    quarter
  ) |>
  summarise(
    avg_temp = mean(tmpf, na.rm = TRUE),
    .groups = "drop"
  )

county_weather <- county_station |>
  select(
    County,
    region,
    station,
    distance_miles
  ) |>
  left_join(
    weather_afternoon,
    by = "station"
  )

county_weekly_weather <- county_weather |>
  group_by(
    County,
    region,
    quarter,
    week
  ) |>
  summarise(
    avg_weekly_temp = mean(avg_temp, na.rm = TRUE),
    .groups = "drop"
  )

region_weekly_weather <- county_weekly_weather |>
  group_by(
    region,
    quarter,
    week
  ) |>
  summarise(
    avg_region_temp = mean(avg_weekly_temp, na.rm = TRUE),
    .groups = "drop"
  )

overall_weekly_weather <- region_weekly_weather |>
  group_by(quarter,
           week) |>
  mutate(overall_temp = mean(avg_region_temp, na.rm = TRUE))
  

ggplot(
  #region_weekly_weather
  overall_weekly_weather,
  aes(
    x = week,
    y = overall_temp
    #y = avg_region_temp
    #color = region
  )
) +
  geom_line(linewidth = 1) +
  geom_vline(
    xintercept = c(14, 27, 40),
    linetype = "dashed",
    alpha = 0.7
  ) +
  labs(
    title = "Seasonal Afternoon Temperature in Iowa in 2025",
    subtitle = "Average Afternoon Temperature (°F)",
    x = "Week",
    y = NULL,
    #color = "Region"
  ) +
  theme_minimal() +
  theme(
    panel.grid.major.x = element_blank(),
    panel.grid.minor.x = element_blank()
  )

