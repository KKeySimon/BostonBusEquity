# Boston Bus Equity Project

## Description of the project:

### We’d like to work on the MBTA Bus Equity Spark! Project.

The goal of this project is to better understand the impact of bus performance on Boston residents by using MBTA bus data to examine service performance trends by geography.

### We will be answering these 4 main questions proposed by the Spark! team.

- What is the ridership per bus route? How has this changed from pre-pandemic to post-pandemic time?
- What are the end-to-end travel times for each bus route in the city?
  - On average, how long does an individual have to wait for a bus (on time vs. delayed)?
  - What is the average delay time of all routes across the entire city?
  - What is the average delay time of the target bus routes (22, 29, 15, 45, 28, 44, 42, 17, 23, 31, 26, 111, 24, 33, 14 - from Livable Streets report)?
- Are there disparities in the service levels of different routes (which lines are late more often than others)?
  - If there are service level disparities, are there differences in the characteristics of the people most impacted (e.g. race, ethnicity, age, income, etc.)?
- Can we chart changes over TIME?
  - Compare the results from 2015-2017 to the most recent survey

## What data needs to be collected and how you will collect it (e.g. scraping xyz website or polling students).

We will be using these 3 data points

Arrival & Departure Times 2024

- https://gis.data.mass.gov/datasets/96c77138c3144906bce93d0257531b6a/about

Ridership by Trip, Season, Route/Line, Stop

- https://mbta-massdot.opendata.arcgis.com/datasets/eec03d901d2e470ebd5758c60d793e8e_0/explore

Arrival & Departure Times By Year

- https://mbta-massdot.opendata.arcgis.com/search?collection=dataset&q=mbta%20bus%20arrival%20departure%20time

## How you plan on modeling the data (e.g. clustering, fitting a linear model, decision trees, XGBoost, some sort of deep learning method, etc.).

- What is the ridership per bus route? How has this changed from pre-pandemic to post-pandemic time?
  - The ridership per bus route in general saw declines across the board after the pandemic. For the bus stops who held relatively low numbers of riders previous to COVID, they remained low, but the stops that were more popular certainly saw a decline in riders post pandemic.
- What are the end-to-end travel times for each bus route in the city?

  - Linear regression model to identify factors that influence travel times.
  - Time series model like ARIMA to forecast travel time trends
  - K-Means clustering to group routes with similar travel time distributions and identify routes with high variability in travel time.

- Are there disparities in the service levels of different routes (which lines are late more often than others)?
  - K-Means clustering to determine which areas have the most lateness or disparities in service levels
- Can we chart changes over TIME?
  - Charting data changes over time doesn’t require predictions and therefore doesn’t need modeling.

## How we plan on visualizing the data:

- What is the ridership per bus route? How has this changed from pre-pandemic to post-pandemic time?
  - Group up data points to represent broader time frames, determining average ridership per bus route at given stops.
    - This would be done on years 2017-2018 and 2022-2023 to see pre and post pandemic effects
  - Create a heatmap to illustrate which routes were being used more prior and post pandemic
    - We can compare map of prior and post to see how much ridership has decreased
- What are the end-to-end travel times for each bus route in the city?
  - Heatmaps to demonstrate travel time variations by route, time of day, and season
  - Time-series Plot for average travel times for bus routes to see anomalies
  - Bar-chart for route travel time comparisons
- Are there disparities in the service levels of different routes (which lines are late more often than others)?
  - Bar chart comparing the averages of the lateness values per route over multiple years
- Can we chart changes over TIME?
  - Clean up MBTA Bus arrival departure times to have the correct dates, create a mapping from stop ID to location for visualization on a map.
  - Visualize range of points to look for extreme outliers (perhaps a car crash occurred) and remove those data points as you want a good range for the heatmap.
  - Each row will represent a 10 minute/1 hour/1 day (whichever is realistic) time frame. We can then put the averages (or median) of the lateness values for each location. We can then use tools like ArcGIS to create a heatmap of which area is most severely effected. We can then create screenshots to create a gif of how the city’s bus lateness changes over time.
  - We can compare survey data by going through each category and comparing (i.e. race, income, language preference), and see how the percentages have changed compared to each other. The 2 survey data are formatted differently (2015-2017 is row based) and (2024 survey is column based) so we should go through and create one to one mappings into one file.
  - We can run this tool on the 2015-2017 data and compare how the visualizations are different.

## What is your test plan?

- What is the ridership per bus route? How has this changed from pre-pandemic to post-pandemic time?
  - Determine what contributes to making a popular bus route
    - Comparing relative population to number of riders
  - Test found attributes to see if certain bus routes are more likely to be popular
- What are the end-to-end travel times for each bus route in the city?
  - Determine if travel time data is normally distributed via the Shapiro-Wilk Test
  - Compare pre-pandemic and post-pandemic travel times
  - Compare travel times across routes
  - Test if factors like time of day, weather, and route length affect travel time or lateness
  - Group routes based on travel time patterns for K-Means clustering
- Are there disparities in the service levels of different routes (which lines are late more often than others)?
  - Test the lateness times for various factors affecting the predicted vs actual route times and determine which factors have the most impact on lateness from the data of each bus stop (race, income, foot traffic)
- Can we chart changes over TIME?
  - Again, a test plan is not necessary as we are not creating predictions for this question, but we can attempt different time frames for each data point to see which visualizations give us the most meaningful insight. We can try including/excluding outliers, and we can try using means/medians for each data point.
