import pandas as pd
import glob
from tqdm import tqdm

file_pattern = "sample_departure_arrival.csv"
csv_files = sorted(glob.glob(file_pattern))

stops = pd.read_csv("stops.csv")

print(csv_files)
total_lateness_results = []
count_results = []
stop_lateness_results = []
stop_count_results = []
lateness_over_time = []
timestamps = [] 
chunk_size = 500000
total_lateness = 0
num_rows = 0
for csv_file in csv_files:
    print(f"Processing {csv_file} in chunks...")

    for chunk_idx, chunk in enumerate(tqdm(pd.read_csv(csv_file, chunksize=chunk_size, encoding='utf-8-sig'))):
        chunk.columns = chunk.columns.str.strip().str.replace("\ufeff", "", regex=False).str.lower()

        chunk.columns = [col.lower().replace("servicedate", "service_date") for col in chunk.columns]
        chunk.columns = ["stop_id" if col.lower() == "stop" else col for col in chunk.columns]
        chunk.columns = ["route_id" if col.lower() == "route" else col for col in chunk.columns]


        # Convert datetime columns
        chunk["service_date"] = pd.to_datetime(chunk["service_date"], errors="coerce")
        chunk = chunk.dropna(subset=["service_date"])

        chunk["month"] = chunk["service_date"].dt.to_period("M").astype(str)

        chunk["scheduled"] = pd.to_datetime(chunk["scheduled"]).dt.strftime("%H:%M:%S")
        chunk["actual"] = pd.to_datetime(chunk["actual"]).dt.strftime("%H:%M:%S")

        chunk["scheduled"] = pd.to_datetime(chunk["service_date"].dt.date.astype(str) + " " + chunk["scheduled"])
        chunk["actual"] = pd.to_datetime(chunk["service_date"].dt.date.astype(str) + " " + chunk["actual"])

        # We ignore earliness as there is no indication of what it means and how it's calculated 
        # in the source (i.e. being late gives positive earliness scores sometimes but usually negative)
        chunk = chunk.drop(columns=["service_date"])

        # calculate our own lateness score which is just in seconds
        chunk["lateness"] = (chunk["actual"] - chunk["scheduled"]).dt.total_seconds()
        total_lateness_per_route = chunk.groupby(["route_id", "month"], as_index=False)["lateness"].sum()
        total_lateness_results.append(total_lateness_per_route)

        route_counts = chunk.groupby(["route_id", "month"], as_index=False).size()
        count_results.append(route_counts)

        total_lateness_per_stop = chunk.groupby(["stop_id", "month"], as_index=False)["lateness"].sum()
        stop_lateness_results.append(total_lateness_per_stop)

        stop_counts = chunk.groupby(["stop_id", "month"], as_index=False).size()
        stop_count_results.append(stop_counts)

        lateness_over_time.extend(chunk["lateness"].values)
        timestamps.extend(chunk["actual"].values)

        final_total_lateness_chunks = pd.concat(total_lateness_results, ignore_index=True)
final_counts_chunks = pd.concat(count_results, ignore_index=True)
final_stop_lateness_chunks = pd.concat(stop_lateness_results, ignore_index=True)
final_stop_counts_chunks = pd.concat(stop_count_results, ignore_index=True)

final_route_total_lateness = final_total_lateness_chunks.groupby(["route_id", "month"], as_index=False)["lateness"].sum()
final_route_counts = final_counts_chunks.groupby(["route_id", "month"], as_index=False).sum()
final_route_summary = final_route_total_lateness.merge(final_route_counts, on=["route_id", "month"], how="left")
final_route_summary["average_lateness"] = final_route_summary["lateness"] / final_route_summary["size"]

# final_route_summary.to_csv("results/final_route_summary.csv", index=False)

final_stop_total_lateness = final_stop_lateness_chunks.groupby(["stop_id", "month"], as_index=False)["lateness"].sum()
final_stop_counts = final_stop_counts_chunks.groupby(["stop_id", "month"], as_index=False).sum()
final_stop_summary = final_stop_total_lateness.merge(final_stop_counts, on=["stop_id", "month"], how="left")
final_stop_summary["average_lateness"] = final_stop_summary["lateness"] / final_stop_summary["size"]
stops["stop_id"] = stops["stop_id"].astype(str)
final_stop_summary["stop_id"] = final_stop_summary["stop_id"].astype(str)


final_stop_summary_with_coords = final_stop_summary.merge(
    stops[["stop_id", "stop_lat", "stop_lon"]], 
    on="stop_id", 
    how="left"
)

# final_stop_summary_with_coords.to_csv("results/final_stop_summary.csv", index=False)

import pandas as pd
import matplotlib.pyplot as plt

final_stop_summary["year"] = final_stop_summary["month"].str[:4].astype(int)
final_route_summary["year"] = final_route_summary["month"].str[:4].astype(int)

# Q1: Stop average lateness by year
print("Q1: Stop average lateness by year")
stop_lateness_by_year = (
    final_stop_summary
    .groupby("year")[["lateness", "size"]]
    .apply(lambda df: df["lateness"].sum() / df["size"].sum())
)
for year, avg in stop_lateness_by_year.items():
    print(f"{year}: {avg:.2f}")

# Q2: Route average lateness by year
print("\nQ2: Route average lateness by year")
route_lateness_by_year = (
    final_route_summary
    .groupby("year")[["lateness", "size"]]
    .apply(lambda df: df["lateness"].sum() / df["size"].sum())
)
for year, avg in route_lateness_by_year.items():
    print(f"{year}: {avg:.2f}")
    