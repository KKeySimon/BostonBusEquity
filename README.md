# Midterm Report & Presentation

## MBTA Bus Arrival Departure Dataset

### Basic Introduction of Datasets

We have access to the expected and actual arrival data everyday from the year 2018-2025. The detail of the data is in minute accuracy and provides a lot of detailed information.

### Preliminary visualizations of data & Detailed description of data processing done so far

A lot of the data processing was a direct consequence by looking at visualizations of data. For example, we later mention how date and time is formatted in the dataset. The format of the data was in DATE (i.e. 2024-01-07) with an included scheduled and actual stop TIME (formatted in 1900-01-01T00:00:04:00Z). The initial dataset was merged to slice off the 1900-01-01 and append the date to the time. But this proved to be inaccurate and was found thanks to visualizations when we visualized lateness over time.

![Lateness Over Time V1](lateness_over_time_v1.png)

The graph above showed very weird consistent pattern of outliers. After writing down these outliers in a csv, we see that the outlier values were around 86400, which is equivalent to being one day late. By visualizing our data, we were easily able to find taht sometimes, if the expected and actual dates are different, the data is formatted so that the day that comes after is formatted as (1900-01-02T00:00:00z).

We then decided to graph the new formatted data that was now fixed. We still see there are outliers and that there are mutliple outliers back to back as shown in the graph below.

![Lateness Over Time Graph](lateness_over_time_v2.png)

We then created a new csv looking for the outlier rows which showed that these outliers and we see they are from the same station back to back. But the intervals between the actual bus time arrivals are the same as the intervals between expected bus time arrivals. We believe that this is most likely some announced shift in the schedule that was not reflected in the spreadsheet. We decided to put an arbitrary threshold of 3600 seconds (1 hour) of lateness or earliness. After we had removed obvious outliers from our dataset, we ended up with the a visualization of the data that looked like the graph below.

![Lateness Over Time](lateness_over_time_v3.png)

We felt the the data looked good enough that we were able to display it onto [ARCGIS](https://bucas.maps.arcgis.com/apps/mapviewer/index.html?webmap=9f60b58427e94c3991bba8cbce9f61ff). The map has a time series player as well and although we've only added 2024 data, the process can be extended to any other year.

We were also able to answer some the questions asked in our initial project proposal such as what is the city wide average lateness which happened to be around 263 seconds late. We were also able to see the average lateness for the target routes asked from the proposal.

| Route ID | Average Lateness (seconds) |
| -------- | -------------------------- |
| 111      | 194.24                     |
| 14       | 292.64                     |
| 15       | 269.35                     |
| 17       | 364.53                     |
| 22       | 380.97                     |
| 23       | 373.58                     |
| 24       | 375.41                     |
| 26       | 154.65                     |
| 28       | 446.06                     |
| 29       | 470.34                     |
| 31       | 258.83                     |
| 33       | 181.59                     |
| 42       | 313.53                     |
| 44       | 403.23                     |
| 45       | 361.81                     |

Again, the data above is from 2024 only as the time it would take to process all the datasets would take a while. But we felt that since this is a midterm report, we can show the result for one year and then process all the data during the final presentation.

### Detailed description of data modeling methods used so far.

The Spark prompt has little to no mentions of using modeling the data, but data modeling will be done for the purpose of this class. The data to be obtained from model can also be very beneficial in predicting future bus delays.

### Preliminary results. (e.g. we fit a linear model to the data and we achieve promising results, or we did some clustering and we notice a clear pattern in the data)
