import pandas as pd

# File patterns for 2018 and 2022 CSV files
file_2018 = "ridership_2018_sample.csv"
file_2022 = "ridership_2022_sample.csv"
chunk_size = 500000
result_df_2018 = pd.DataFrame()  # DataFrame for 2018
result_df_2022 = pd.DataFrame()  # DataFrame for 2022

# Process the 2018 CSV file
for chunk in pd.read_csv(file_2018, chunksize=chunk_size):
    chunk.columns = chunk.columns.str.strip().str.lower()
    chunk['year'] = chunk['season'].str.extract(r'(\d{4})').astype(int)
    chunk['time_period'] = chunk['year'].apply(lambda x: '2018' if x == 2018 else 'Other')
    chunk_avg = chunk.groupby(['route_id', 'time_period'])['boardings'].sum().reset_index()
    result_df_2018 = pd.concat([result_df_2018, chunk_avg])

# Process the 2022 CSV file
for chunk in pd.read_csv(file_2022, chunksize=chunk_size):
    chunk.columns = chunk.columns.str.strip().str.lower()
    chunk['year'] = chunk['season'].str.extract(r'(\d{4})').astype(int)
    chunk['time_period'] = chunk['year'].apply(lambda x: '2022' if x == 2022 else 'Other')
    chunk_avg = chunk.groupby(['route_id', 'time_period'])['boardings'].sum().reset_index()
    result_df_2022 = pd.concat([result_df_2022, chunk_avg])

# Combine the results from both years
final_df = pd.concat([result_df_2018, result_df_2022])

# Final aggregation by route and time period
final_avg = final_df.groupby(['route_id', 'time_period'])['boardings'].sum().reset_index()

# Filter to include only routes that have both 2018 and 2022 data
route_seasons = final_avg.groupby('route_id')['time_period'].apply(set)
valid_routes = route_seasons[route_seasons.apply(lambda x: {'2018', '2022'}.issubset(x))].index

# Filter the final DataFrame to include only valid routes
filtered_df = final_avg[final_avg['route_id'].isin(valid_routes)]

# Pivot the data to have '2018' and '2022' as columns for each route
pivoted_df = filtered_df.pivot(index='route_id', columns='time_period', values='boardings')

# Calculate the absolute change between '2022' and '2018'
pivoted_df['absolute_change'] = pivoted_df['2022'] - pivoted_df['2018']

# Reset index for clean formatting
pivoted_df.reset_index(inplace=True)

# Show the results with the absolute change
print(pivoted_df[['route_id', '2018', '2022', 'absolute_change']])

# Calculate the median absolute change across all routes
average_percent_change = pivoted_df['absolute_change'].median()
print(f"The average percent change across all routes is: {average_percent_change:.2f}")

# ---- ADDING TRAFFIC PER STOP PROCESSING FOR 2018 ----

# Load and process stop coordinates and ridership data for 2018
stops = pd.read_csv("stops.csv")

# Processing the ridership data for 2018
df_2018 = pd.read_csv(file_2018)

df_2018['year'] = df_2018['season'].str.extract(r'(\d{4})').astype(float)
df_2018 = df_2018[df_2018['year'] == 2018]  # Only focus on 2018 data

# Grouping and aggregating ridership data by route_id and stop_id for 2018
aggregated_ridership = df_2018.groupby(['route_id', 'stop_id']).agg({
    'boardings': 'sum', 
    'alightings': 'sum'
}).reset_index()

# Calculate total traffic (boardings + alightings) per stop
aggregated_ridership['traffic'] = aggregated_ridership['boardings'] + aggregated_ridership['alightings']

# Load stop coordinates for 2018
stops['route'] = stops['stop_desc'].astype(str)
stops = stops.dropna(subset=['route'])
merged_coordinates = stops.groupby('stop_id', as_index=False).agg({
    'stop_lat': 'first',
    'stop_lon': 'first'
})

# Merge the stop coordinates with aggregated ridership data
final_ridership_data = pd.merge(aggregated_ridership, merged_coordinates, on='stop_id', how='left')

# Show the processed data for 2018
print(final_ridership_data[['route_id', 'stop_id', 'traffic', 'stop_lat', 'stop_lon']].head())

# Outlier Detection (Using IQR method to detect high/low traffic outliers)
Q1 = final_ridership_data['traffic'].quantile(0.25)
Q3 = final_ridership_data['traffic'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = max(0, Q1 - 1.5 * IQR)
upper_bound = Q3 + 1.5 * IQR

low_outliers = final_ridership_data[final_ridership_data['traffic'] < lower_bound]
high_outliers = final_ridership_data[final_ridership_data['traffic'] > upper_bound]
normal_data = final_ridership_data[(final_ridership_data['traffic'] >= lower_bound) & 
                                   (final_ridership_data['traffic'] <= upper_bound)]

# Show the outliers data
print(f"Low traffic outliers (below {lower_bound}):")
print(low_outliers[['route_id', 'stop_id', 'traffic', 'stop_lat', 'stop_lon']])

print(f"\nHigh traffic outliers (above {upper_bound}):")
print(high_outliers[['route_id', 'stop_id', 'traffic', 'stop_lat', 'stop_lon']])

# Final DataFrame to CSV (Optional)
final_ridership_data.to_csv("final_ridership_2018_data.csv", index=False)
