import pandas as pd

# File paths for 2018 and 2022 CSV files
file_2018 = "./test_data/ridership_2018_sample.csv" 
file_2022 = "./test_data/ridership_2022_sample.csv"
chunk_size = 500000
result_df_2018 = pd.DataFrame()
result_df_2022 = pd.DataFrame()

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
filtered_df = final_avg[final_avg['route_id'].isin(valid_routes)]

# Pivot to get 2018 and 2022 side-by-side
pivoted_df = filtered_df.pivot(index='route_id', columns='time_period', values='boardings')
pivoted_df['absolute_change'] = pivoted_df['2022'] - pivoted_df['2018']
pivoted_df.reset_index(inplace=True)

# Print results
print(pivoted_df[['route_id', '2018', '2022', 'absolute_change']])
average_percent_change = pivoted_df['absolute_change'].median()
print(f"The average percent change across all routes is: {average_percent_change:.2f}")

# ---- Process Traffic Per Stop for 2018 ----

# Load stop coordinates
stops = pd.read_csv("stops.csv")
stops['route'] = stops['stop_desc'].astype(str)
stops = stops.dropna(subset=['route'])

# Extract coordinates per stop
merged_coordinates = stops.groupby('stop_id', as_index=False).agg({
    'stop_lat': 'first',
    'stop_lon': 'first'
})

# Load full 2018 data for stop-level aggregation
df_2018 = pd.read_csv(file_2018)
df_2018.columns = df_2018.columns.str.strip().str.lower()
df_2018['year'] = df_2018['season'].str.extract(r'(\d{4})').astype(float)
df_2018 = df_2018[df_2018['year'] == 2018]

# Aggregate ridership by stop
aggregated_ridership = df_2018.groupby(['route_id', 'stop_id']).agg({
    'boardings': 'sum', 
    'alightings': 'sum'
}).reset_index()
aggregated_ridership['traffic'] = aggregated_ridership['boardings'] + aggregated_ridership['alightings']

# Ensure stop_id types match for merge
aggregated_ridership['stop_id'] = aggregated_ridership['stop_id'].astype(str)
merged_coordinates['stop_id'] = merged_coordinates['stop_id'].astype(str)

# Merge with coordinates
final_ridership_data = pd.merge(aggregated_ridership, merged_coordinates, on='stop_id', how='left')

# Print processed data
print(final_ridership_data[['route_id', 'stop_id', 'traffic', 'stop_lat', 'stop_lon']].head())

# IQR outlier detection
Q1 = final_ridership_data['traffic'].quantile(0.25)
Q3 = final_ridership_data['traffic'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = max(0, Q1 - 1.5 * IQR)
upper_bound = Q3 + 1.5 * IQR

low_outliers = final_ridership_data[final_ridership_data['traffic'] < lower_bound]
high_outliers = final_ridership_data[final_ridership_data['traffic'] > upper_bound]

print(f"Low traffic outliers (below {lower_bound}):")
print(low_outliers[['route_id', 'stop_id', 'traffic', 'stop_lat', 'stop_lon']])

print(f"\nHigh traffic outliers (above {upper_bound}):")
print(high_outliers[['route_id', 'stop_id', 'traffic', 'stop_lat', 'stop_lon']])

# Optional: Save to CSV
final_ridership_data.to_csv("final_ridership_2018_data.csv", index=False)
