import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from IPython.display import display
import glob
from tqdm import tqdm
import os


# all the export files in 2015-2017
precovid_folder = "ridership_data/2015-2017-tables"
print("Folder contents:", os.listdir(precovid_folder))
file_pattern = os.path.join(precovid_folder, "*.xlsx")
file_paths   = sorted(glob.glob(file_pattern))
print("Found Excel files:", file_paths)

df_list = [pd.read_excel(file) for file in file_paths]
df_pre = pd.concat(df_list, ignore_index=True)

df_pre.head()

postcovid = os.path.join("ridership_data", "2023.csv")
df_post = pd.read_csv(postcovid)
df_post = df_post[df_post['service_mode'] == 'Bus']

df_pre_numeric = df_pre.drop(columns=["Mode"], errors="ignore").apply(pd.to_numeric, errors="coerce")

# mapping of categories from df_post
df_post.columns = df_post.columns.str.strip().str.lower()
df_post['full_category'] = df_post['measure_group'] + ": " + df_post['category']

category_mapping = df_post[['category', 'full_category']].drop_duplicates().set_index('category').to_dict()['full_category']

# rename df_pre columns using this mapping
df_post.rename(columns=lambda x: x.strip(), inplace=True)
df_post.rename(columns={
    'weighted_percent': 'percentage'
}, inplace=True)


df_pre.columns, df_post.columns

df_post = df_post.dropna()
df_pre = df_pre.dropna()

df_post.columns = df_post.columns.str.strip().str.lower()
df_post.rename(columns={'weighted_percent': 'percentage'}, inplace=True)
df_post["percentage"] = df_post["percentage"] * 100

df_post['full_category'] = df_post['measure'] + ": " + df_post['category']

# extract unique category names from df_post for renaming df_pre
category_mapping = df_post[['category', 'full_category']].drop_duplicates().set_index('category').to_dict()['full_category']

# drop non-numeric columns from df_pre and convert all to numeric
df_pre_numeric = df_pre.drop(columns=["Mode"], errors="ignore").apply(pd.to_numeric, errors="coerce")

category_totals = df_pre_numeric.groupby(lambda x: x.split(":")[0], axis=1).sum()
pre_percentages = df_pre_numeric.apply(lambda x: (x / category_totals[x.name.split(":")[0]]) * 100 if x.name.split(":")[0] in category_totals else x, axis=0)
pre_percentages = pre_percentages.rename(columns=category_mapping)

# convert to DataFrame for merging
pre_percentages = pre_percentages.T
pre_percentages = pre_percentages.reset_index()
pre_percentages = pre_percentages.rename(columns={pre_percentages.columns[0]: 'pre_covid_percent'})
pre_percentages['full_category'] = pre_percentages.index
pre_percentages = pre_percentages.reset_index(drop=True)

# ensure both merge columns are strings
pre_percentages["full_category"] = pre_percentages["full_category"].astype(str)
df_post["full_category"] = df_post["full_category"].astype(str)

# merge with df_post based on full_category
df_comparison = pd.merge(
    pre_percentages,
    df_post[['measure_group', 'full_category', 'percentage']],
    on="full_category",
    how="inner"
)

# create separate tables for each measure_group
grouped_tables = {measure: data for measure, data in df_comparison.groupby("measure_group")}

# display
for measure, table in grouped_tables.items():
    print(f"\nComparison Table for {measure}:")
    display(table)

# apply category_mapping to rename pre-covid columns BEFORE calculating percentages
df_pre_renamed = df_pre.rename(columns=category_mapping)

# drop non-numeric and compute percentages by category
df_pre_numeric = df_pre_renamed.drop(columns=["Route"], errors="ignore").apply(pd.to_numeric, errors="coerce")
category_totals = df_pre_numeric.groupby(lambda x: x.split(":")[0], axis=1).sum()
pre_percentages = df_pre_numeric.apply(lambda x: (x / category_totals[x.name.split(":")[0]]) * 100 if x.name.split(":")[0] in category_totals else x, axis=0)

# turn into long-form DataFrame
pre_percentages["Route"] = df_pre["Route"]
pre_melted = pre_percentages.melt(id_vars="Route", var_name="full_category", value_name="pre_covid_percent")

folder = "test_data"
pattern = "test_arrivals_2023.csv"
file_pattern = os.path.join(folder, pattern)

file_paths = sorted(glob.glob(file_pattern))

# variables for chunk processing
chunksize = 500000
route_lateness = []
route_counts = []
route_ids = []

outlier_threshold = 3600  # outlier threshold of 1 hour in seconds

# ensure we have files
if not file_paths:
    print("No CSV files found. Check the file path!")

# process each file in the folder
for file_path in file_paths:
    print(f"Processing: {file_path}", flush=True)
    
    for chunk in tqdm(pd.read_csv(file_path, chunksize=chunksize), desc=f"Processing {file_path}"):
        # Convert time columns and remove invalid entries
        chunk["service_date"] = pd.to_datetime(chunk["service_date"], errors="coerce")
        chunk["scheduled"] = pd.to_datetime(chunk["scheduled"], errors="coerce")
        chunk["actual"] = pd.to_datetime(chunk["actual"], errors="coerce")
        chunk.dropna(subset=["service_date", "scheduled", "actual"], inplace=True)

        chunk["service_date"] = chunk["service_date"].dt.tz_localize(None)
        chunk["scheduled"] = chunk["scheduled"].dt.tz_localize(None)
        chunk["actual"] = chunk["actual"].dt.tz_localize(None)

        # Use reference time for accurate lateness calculation
        reference_time = pd.Timestamp("1900-01-01 00:00:00").tz_localize(None)
        chunk["scheduled_seconds"] = (chunk["scheduled"] - reference_time).dt.total_seconds()
        chunk["actual_seconds"] = (chunk["actual"] - reference_time).dt.total_seconds()

        # Adjust timestamps using service_date
        chunk["scheduled"] = chunk["service_date"] + pd.to_timedelta(chunk["scheduled_seconds"], unit="s")
        chunk["actual"] = chunk["service_date"] + pd.to_timedelta(chunk["actual_seconds"], unit="s")

        # Compute lateness
        chunk["lateness"] = (chunk["actual"] - chunk["scheduled"]).dt.total_seconds()

        # **Filter Outliers (Keep values within -1 hour to +1 hour)**
        chunk = chunk[chunk["lateness"].abs() <= outlier_threshold]

        # Group by route_id (sum of lateness, count of trips)
        grouped = chunk.groupby(["route_id"])["lateness"].agg(["sum", "count"]).reset_index()

        # Store results
        if not grouped.empty:
            route_lateness.append(grouped["sum"].values)
            route_counts.append(grouped["count"].values)
            route_ids.append(grouped["route_id"].values)

# debugging print to check data collected
print(f"Route lateness collected: {len(route_lateness)}")
print(f"Route counts collected: {len(route_counts)}")
print(f"Route IDs collected: {len(route_ids)}")

# aggregate results
total_lateness = sum(map(sum, route_lateness)) if route_lateness else 0
total_counts = sum(map(sum, route_counts)) if route_counts else 0
average_lateness = total_lateness / total_counts if total_counts > 0 else 0  # Avoid division by zero

# create DataFrame for route lateness
lateness_df = pd.DataFrame({
    "route_id": np.concatenate(route_ids) if route_ids else [],
    "total_lateness": np.concatenate(route_lateness) if route_lateness else [],
    "trip_count": np.concatenate(route_counts) if route_counts else []
})

# average lateness per route
if not lateness_df.empty:
    lateness_df["average_lateness"] = lateness_df["total_lateness"] / lateness_df["trip_count"]

# we want to use the routes with lateness that is above average in order answer the question of what demographic of people are affected most by lateness
above_avg_routes = lateness_df[lateness_df["average_lateness"] > average_lateness] if not lateness_df.empty else pd.DataFrame()

# display results
print(f"Citywide Average Lateness: {average_lateness:.2f} seconds")
print("\nRoutes with above-average lateness:")
print(above_avg_routes)

# Pre covid with 2018 dataset
# using simon's code computing lateness now for 2018 arrivals and departures
folder = "test_data"
pattern = "test_arrivals_2018.csv"
file_pattern2 = os.path.join(folder, pattern)

file_paths2 = sorted(glob.glob(file_pattern2))

chunksize = 500000
route_lateness2 = []
route_counts2 = []
route_ids2 = []

outlier_threshold = 3600

if not file_paths2:
    print("No CSV files found. Check the file path!")

for file_path in file_paths2:
    print(f"Processing: {file_path}", flush=True)
    
    for chunk in tqdm(pd.read_csv(file_path, chunksize=chunksize), desc=f"Processing {file_path}"):
        # Convert time columns and remove invalid entries
        chunk["service_date"] = pd.to_datetime(chunk["service_date"], errors="coerce")
        chunk["scheduled"] = pd.to_datetime(chunk["scheduled"], errors="coerce")
        chunk["actual"] = pd.to_datetime(chunk["actual"], errors="coerce")
        chunk.dropna(subset=["service_date", "scheduled", "actual"], inplace=True)

        # Ensure proper timezone handling (remove timezone info if necessary)
        chunk["service_date"] = chunk["service_date"].dt.tz_localize(None)
        chunk["scheduled"] = chunk["scheduled"].dt.tz_localize(None)
        chunk["actual"] = chunk["actual"].dt.tz_localize(None)

        # Use reference time for accurate lateness calculation
        reference_time = pd.Timestamp("1900-01-01 00:00:00").tz_localize(None)
        chunk["scheduled_seconds"] = (chunk["scheduled"] - reference_time).dt.total_seconds()
        chunk["actual_seconds"] = (chunk["actual"] - reference_time).dt.total_seconds()

        # Adjust timestamps using service_date
        chunk["scheduled"] = chunk["service_date"] + pd.to_timedelta(chunk["scheduled_seconds"], unit="s")
        chunk["actual"] = chunk["service_date"] + pd.to_timedelta(chunk["actual_seconds"], unit="s")

        # Compute lateness
        chunk["lateness"] = (chunk["actual"] - chunk["scheduled"]).dt.total_seconds()

        # **Filter Outliers (Keep values within -1 hour to +1 hour)**
        chunk = chunk[chunk["lateness"].abs() <= outlier_threshold]

        # Group by route_id (sum of lateness, count of trips)
        grouped = chunk.groupby(["route_id"])["lateness"].agg(["sum", "count"]).reset_index()

        # Store results
        if not grouped.empty:
            route_lateness2.append(grouped["sum"].values)
            route_counts2.append(grouped["count"].values)
            route_ids2.append(grouped["route_id"].values)

# debugging print to check data collected
print(f"Route lateness collected: {len(route_lateness2)}")
print(f"Route counts collected: {len(route_counts2)}")
print(f"Route IDs collected: {len(route_ids2)}")

# aggregate results
total_lateness2 = sum(map(sum, route_lateness2)) if route_lateness2 else 0
total_counts2 = sum(map(sum, route_counts2)) if route_counts2 else 0
average_lateness2 = total_lateness2 / total_counts2 if total_counts2 > 0 else 0  # Avoid division by zero

# create DataFrame for route lateness
lateness_df2 = pd.DataFrame({
    "route_id": np.concatenate(route_ids2) if route_ids2 else [],
    "total_lateness": np.concatenate(route_lateness2) if route_lateness2 else [],
    "trip_count": np.concatenate(route_counts2) if route_counts2 else []
})

# calculate average lateness per route
if not lateness_df2.empty:
    lateness_df2["average_lateness"] = lateness_df2["total_lateness"] / lateness_df2["trip_count"]

# we want to use the routes with lateness that is above average in order answer the question of what demographic of people are affected most by lateness
above_avg_routes_2018 = lateness_df2[lateness_df2["average_lateness"] > average_lateness2] if not lateness_df2.empty else pd.DataFrame()

# display results
print(f"Citywide Average Lateness: {average_lateness2:.2f} seconds")
print("\nRoutes with above-average lateness:")
print(above_avg_routes_2018)

postcovid = os.path.join("ridership_data", "2023.csv")
df_post = pd.read_csv(postcovid)

# we only want the bus data
df_post = df_post[df_post['service_mode'] == 'Bus']

# convert route_id to match post-COVID dataset format
above_avg_routes = above_avg_routes.copy()  # Ensure it's a copy
above_avg_routes["route_id"] = above_avg_routes["route_id"].astype(str)

df_post["reporting_group"] = df_post["reporting_group"].astype(str)

# merge post-COVID data with routes that had above-average lateness
df_analysis = df_post[df_post["reporting_group"].isin(above_avg_routes["route_id"])]

print("\nRoutes with Higher Than Average Lateness:")
display(above_avg_routes)

# aggregate percentage data for routes with high lateness
# for post covid
category_analysis = df_analysis.groupby(["measure_group", "category"])["weighted_percent"].mean().reset_index()

# sort
top_categories = (
    category_analysis
    .sort_values(['measure_group', 'weighted_percent'], ascending=[True, False])
    .groupby("measure_group")
    .head(3)
)

# Visualizing the top characteristics
palette = sns.color_palette("tab20", n_colors=50)
unique_categories = top_categories["category"].unique()
category_to_color = {cat: palette[i % len(palette)] for i, cat in enumerate(unique_categories)}


top_categories["Position"] = top_categories.groupby("measure_group").cumcount()

fig, ax = plt.subplots(figsize=(15, 6))
groups = top_categories["measure_group"].unique()
x = np.arange(len(groups))
width = 0.25

for i in range(3):
    subset = top_categories[top_categories["Position"] == i] 
    if subset.empty:
        continue  # Prevent shape mismatch errors

    bars = ax.bar(
        x + (i - 1) * width,
        subset["weighted_percent"],
        width=width,
        color=[category_to_color[cat] for cat in subset["category"]],
        label=None
    )


ax.set_xticks(x)
ax.set_xticklabels(groups, rotation=45, ha="right")
ax.set_ylabel("Average Percentage in High-Lateness Routes")
ax.set_title("Top 3 Characteristics per Measure Group (Post-COVID High-Lateness Routes)")

handles = [plt.Line2D([0], [0], marker='o', color='w', label=cat,
                      markerfacecolor=color, markersize=10)
           for cat, color in category_to_color.items()]
ax.legend(handles=handles, title="Category", bbox_to_anchor=(1.05, 1), loc='upper left')

ax.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# display the top categories
top_10 = category_analysis.head(10)
print("Top 10 Categories with Highest Average Percentages in High-Lateness Routes (Post-COVID):\n")
print(top_10.to_string(index=False))

df_post["full_category"] = df_post["measure"] + ": " + df_post["category"]
df_post["weighted_percent"] = df_post["weighted_percent"] * 100

# NOW filter using the updated df_post
df_analysis = df_post[df_post["reporting_group"].isin(above_avg_routes["route_id"])]

# pivot to get categories as features
pivot_df = df_analysis.pivot_table(index='reporting_group', 
                                    columns='full_category', 
                                    values='weighted_percent', 
                                    aggfunc='mean').fillna(0)

# Ensure merge keys are both string type
pivot_df.index = pivot_df.index.astype(str)
lateness_df["route_id"] = lateness_df["route_id"].astype(str)

# Merge on route_id (now as string)
pivot_df = pivot_df.merge(
    lateness_df[["route_id", "average_lateness"]],
    left_index=True, right_on="route_id", how="left"
)

pivot_df = pivot_df.drop(columns="route_id")

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaled_features = scaler.fit_transform(pivot_df)

#normalizing the features
from sklearn.cluster import KMeans

#kmeans
kmeans = KMeans(n_clusters=3, random_state=42)
clusters = kmeans.fit_predict(scaled_features)

pivot_df["cluster"] = clusters

# Show average feature values per cluster
cluster_summary = pivot_df.groupby("cluster").mean()
display(cluster_summary)

sns.boxplot(data=pivot_df, x="cluster", y="average_lateness")
plt.title("Average Lateness by Cluster")
plt.show()

from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

# Reduce to 2D using PCA
pca = PCA(n_components=2)
reduced_features = pca.fit_transform(scaled_features)

# Create a DataFrame with 2D coordinates and cluster labels
visual_df = pd.DataFrame(reduced_features, columns=["PCA1", "PCA2"])
visual_df["Cluster"] = clusters

# Plot the clusters in 2D space
plt.figure(figsize=(10, 6))
sns.scatterplot(data=visual_df, x="PCA1", y="PCA2", hue="Cluster", palette="Set2", s=70)
plt.title("K-Means Clustering of Bus Routes (Demographics) - PCA Projection")
plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.legend(title="Cluster")
plt.grid(True)
plt.show()

cluster_summary = pivot_df.groupby("cluster").mean()
display(cluster_summary)

#pre covid lateness using the survey dataset 2015-2017 and the departure arrivals from 2018 (closest dataset)
precovid_folder = "ridership_data/2015-2017-tables"
print("Folder contents:", os.listdir(precovid_folder))
file_pattern = os.path.join(precovid_folder, "*export.xlsx")
file_paths   = sorted(glob.glob(file_pattern))
print("Found Excel files:", file_paths)

df_list = [pd.read_excel(file) for file in file_paths]
df_pre = pd.concat(df_list, ignore_index=True)

df_pre["Route"] = df_pre["Route"].astype(str)

df_analysis2 = df_pre[df_pre["Route"].isin(above_avg_routes_2018["route_id"])]


#pre covid lateness using the survey dataset 2015-2017 and the departure arrivals from 2018 (closest dataset)
precovid_folder = "ridership_data/2015-2017-tables"
print("Folder contents:", os.listdir(precovid_folder))
file_pattern = os.path.join(precovid_folder, "*export.xlsx")
file_paths   = sorted(glob.glob(file_pattern))

df_list = [pd.read_excel(file) for file in file_paths]
df_pre = pd.concat(df_list, ignore_index=True)

# Convert route_id to match post-COVID dataset format
above_avg_routes_2018 = above_avg_routes_2018.copy()
above_avg_routes_2018["route_id"] = above_avg_routes_2018["route_id"].astype(str)

df_pre["Route"] = df_pre["Route"].astype(str)

# Merge post-COVID data with routes that had above-average lateness
df_analysis2 = df_pre[df_pre["Route"].isin(above_avg_routes_2018["route_id"])]

print("\nRoutes with Higher Than Average Lateness 2018:")
display(above_avg_routes_2018) 


precovid_folder = "ridership_data/2015-2017-tables"
print("Folder contents:", os.listdir(precovid_folder))
file_pattern = os.path.join(precovid_folder, "*export.xlsx")
file_paths   = sorted(glob.glob(file_pattern))
print("Found Excel files:", file_paths)

top_categories_per_table = {}
late_ids = above_avg_routes_2018["route_id"].astype(str).unique()

for file_path in file_paths:
    df = pd.read_excel(file_path)

    # clean headers & route col
    df.columns = df.columns.str.strip()
    if "Route" not in df.columns:
        continue
    df["Route"] = df["Route"].astype(str)

    # keep only the late routes
    df_filt = df[df["Route"].isin(late_ids)].copy()

    # numeric survey columns already contain % values
    numeric_cols = (
        df_filt
        .select_dtypes("number")
        .columns
        .difference(["Route"])
    )
    if numeric_cols.empty:
        continue

    category_avgs = (
        df_filt[numeric_cols]
        .mean()
        .sort_values(ascending=False)
    )

    tbl_name = os.path.basename(file_path).replace("_data_export.xlsx", "")
    top_categories_per_table[tbl_name] = category_avgs

# quick display
for tbl, ser in top_categories_per_table.items():
    print(f"\nTop categories for {tbl}:")
    display(ser.head(2))

import pandas as pd
import glob
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1) Read in all pre-COVID survey tables
precovid_folder = "ridership_data/2015-2017-tables"
file_paths = sorted(glob.glob(os.path.join(precovid_folder, "*export.xlsx")))
if not file_paths:
    raise FileNotFoundError(f"No Excel files found in {precovid_folder}")

# ensure your late‐route IDs are strings
late_ids = above_avg_routes_2018["route_id"].astype(str).unique()

# 2) For each table, filter to late routes and compute the mean % per survey column
rows = []
for fp in file_paths:
    table_name = os.path.splitext(os.path.basename(fp))[0]
    df = pd.read_excel(fp)
    if "Route" not in df.columns:
        continue
    df["Route"] = df["Route"].astype(str)
    df = df[df["Route"].isin(late_ids)]
    # pick only numeric columns (the % columns)
    num_cols = df.select_dtypes(include=[np.number]).columns.difference(["Route"])
    if num_cols.empty:
        continue
    means = df[num_cols].mean()  # average percent per category
    # grab top 3
    for cat, pct in means.nlargest(3).items():
        rows.append({
            "measure_group": table_name,
            "category": cat,
            "percent": pct
        })

precovid_top = pd.DataFrame(rows)
if precovid_top.empty:
    raise ValueError("No pre-COVID rows after filtering to late routes!")

# 3) Build color map
palette = sns.color_palette("tab20", n_colors=50)
unique_cats = precovid_top["category"].unique()
category_to_color = {cat: palette[i % len(palette)] for i, cat in enumerate(unique_cats)}

# 4) Position for grouped bar chart
precovid_top["Position"] = precovid_top.groupby("measure_group").cumcount()

fig, ax = plt.subplots(figsize=(15, 6))
groups = precovid_top["measure_group"].unique()
x = np.arange(len(groups))
width = 0.25

for i in range(3):
    subset = precovid_top[precovid_top["Position"] == i]
    if subset.empty:
        continue
    ax.bar(
        x + (i - 1) * width,
        subset["percent"],
        width=width,
        color=[category_to_color[cat] for cat in subset["category"]],
        label=None
    )

ax.set_xticks(x)
ax.set_xticklabels(groups, rotation=45, ha="right")
ax.set_ylabel("Average Percentage in High-Lateness Routes")
ax.set_title("Top 3 Survey Categories per Table (Pre-COVID High-Lateness Routes)")

# legend
handles = [
    plt.Line2D([0], [0], marker='o', color='w', label=cat,
               markerfacecolor=col, markersize=10)
    for cat, col in category_to_color.items()
]
ax.legend(handles=handles, title="Category", bbox_to_anchor=(1.05, 1), loc='upper left')

ax.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()


ax.set_xticks(x)
ax.set_xticklabels(groups, rotation=45, ha="right")
ax.set_ylabel("Average Percentage in High-Lateness Routes")
ax.set_title("Top 3 Characteristics per Measure Group (Post-COVID High-Lateness Routes)")

handles = [plt.Line2D([0], [0], marker='o', color='w', label=cat,
                      markerfacecolor=color, markersize=10)
           for cat, color in category_to_color.items()]
ax.legend(handles=handles, title="Category", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.show()

df_post.columns = df_post.columns.str.strip().str.lower()
df_post['full_category'] = df_post['measure_group'].str.strip() + ": " + df_post['category'].str.strip()

# Filter to high-lateness routes
above_avg_route_ids = above_avg_routes_2018["route_id"].astype(str).unique()
df_post_filtered = df_post[df_post["reporting_group"].astype(str).isin(above_avg_route_ids)]

# Aggregate post-COVID percentages
post_averages = (
    df_post_filtered.groupby("full_category")["weighted_percent"]
    .mean()
    .reset_index()
    .rename(columns={"percentage": "post_covid_percent"})
)

# collect top pre-COVID categories
records = []
for table, series in top_categories_per_table.items():
    for category, pre_pct in series.head(2).items():
        records.append({
            "table": table,
            "full_category": category.strip(),  # clean here too
            "pre_covid_percent": pre_pct
        })

df_top_categories = pd.DataFrame(records)

def normalize(text):
    return str(text).strip().lower().replace("–", "-")

postcovid = os.path.join("ridership_data", "2023.csv")
df_post = pd.read_csv(postcovid)

# Standardize column names
df_post.columns = df_post.columns.str.strip().str.lower()

# Filter only bus routes
df_post = df_post[df_post["service_mode"] == "Bus"]

# Rename and scale percentage
df_post.rename(columns={"weighted_percent": "percentage"}, inplace=True)
df_post["percentage"] *= 100

late_ids = above_avg_routes_2018["route_id"].astype(str).unique()
df_post = df_post[df_post["reporting_group"].astype(str).isin(late_ids)]

# Build combined category label using MEASURE instead of measure_group
df_post["full_category"] = df_post["measure"] + ": " + df_post["category"]

# Use entire dataset for analysis
df_analysis = df_post.copy()

# Group and compute averages by MEASURE and category
category_analysis = (
    df_analysis
    .groupby(["measure", "category"])["percentage"]
    .mean()
    .reset_index()
)

# Use MEASURE instead of measure_group to build full_category
category_analysis["full_category"] = category_analysis["measure"].str.strip() + ": " + category_analysis["category"].str.strip()

# Normalize
import re
def normalize(text):
    if pd.isnull(text):
        return ""
    text = str(text).strip().lower()
    text = re.sub(r"[–—−]", "-", text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace(":", ": ")
    return text.strip()

category_analysis["full_category_clean"] = category_analysis["full_category"].apply(normalize)

#Prepare pre-COVID top categories
records = []
for table, series in top_categories_per_table.items():
    for category, pre_pct in series.head(2).items():
        records.append({
            "table": table,
            "full_category": category.strip(),
            "pre_covid_percent": pre_pct,
            "full_category_clean": normalize(category)
        })

df_top_categories = pd.DataFrame(records)

print("\nTop pre-COVID categories:")
print(df_top_categories["full_category_clean"].sort_values().unique())

print("\nPost-COVID categories (from category_analysis):")
print(category_analysis["full_category_clean"].sort_values().unique())

# Normalize
df_top_categories["full_category_clean"] = df_top_categories["full_category"].apply(normalize)
category_analysis["full_category_clean"] = category_analysis["full_category"].apply(normalize)

# filter the pre covid categories so only the relevant/important categories are kept
keep_categories = ['access:  walked or bicycled', 'english ability:  always', 'gender:  woman', 'hispanic:  no', 
               'low-income:  no', 'low-income:  yes', 'race:  white', 'trip frequency:  5 days a week', 
               'trip purpose:  home-based work', ]
print("Available pre-COVID categories:", df_top_categories["full_category_clean"].unique())
print("Filtering against keep_categories:", keep_categories)

df_top_categories = df_top_categories[df_top_categories["full_category_clean"].isin(keep_categories)]

# Sanity check
print("\nFiltered pre-COVID categories:")
print(df_top_categories["full_category_clean"].sort_values().unique())

# Manually mapping post-COVID full_category_clean to pre-COVID equivalent
manual_map = {
    "access to first mbta service:  walked": "access: walked or bicycled",
    'gender:  woman': 'gender: woman',
    'race:  white': 'race:  white',
    "access to first mbta service:  bike, scooter or other micromobility": "access: walked or bicycled",
    "ability to understand english:  always": 'english ability: always',
    "hispanic or latino/latina:  no": "hispanic: no",
    "title vi low-income:  no": 'low-income: no',
    "title vi low-income:  yes": 'low-income: yes',
    "frequency:  5 days per week": 'trip frequency: 5 days a week',
    'trip purpose:  home-based work': 'trip purpose: home-based work'
}
category_analysis["full_category_clean_mapped"] = category_analysis["full_category_clean"].replace(manual_map)
# Group by the new mapped category and average the percentage
post_averages = (
    category_analysis
    .groupby("full_category_clean_mapped")["percentage"]
    .mean()
    .reset_index()
    .rename(columns={"full_category_clean_mapped": "full_category_clean", "percentage": "post_covid_percent"})
)
keep_categories = [normalize(x) for x in keep_categories]
df_top_categories["full_category_clean"] = df_top_categories["full_category_clean"].apply(normalize)
category_analysis["full_category_clean"] = category_analysis["full_category_clean"].apply(normalize)

print("Pre-COVID Percentages")
display(
    df_top_categories[["full_category_clean", "pre_covid_percent"]]
    .sort_values(by="full_category_clean")
    .reset_index(drop=True)
)

manual_map_normalized = {
    normalize(k): normalize(v) for k, v in manual_map.items()
}

# Step 2: Apply normalization and mapping to category_analysis
category_analysis["full_category_clean"] = category_analysis["full_category"].apply(normalize)
category_analysis["full_category_clean_mapped"] = category_analysis["full_category_clean"].replace(manual_map_normalized)

# Step 3: Filter only rows that came from manual_map keys
mapped_keys = list(manual_map_normalized.keys())
post_filtered = category_analysis[
    category_analysis["full_category_clean"].isin(mapped_keys)
]

# Step 4: Group and average post-COVID percentages
post_summary = (
    post_filtered
    .groupby("full_category_clean_mapped")["percentage"]
    .mean()
    .reset_index()
    .rename(columns={"full_category_clean_mapped": "full_category_clean", "percentage": "post_covid_percent"})
)

# Step 5: Display the filtered post-COVID data
print("Mapped Post-COVID Categories Only")
display(post_summary.sort_values(by="full_category_clean").reset_index(drop=True))


# Step 1: Prepare the data
# Stack pre and post COVID percentages into a single dataframe
pre_covid_plot = df_top_categories[["full_category_clean", "pre_covid_percent"]].copy()
pre_covid_plot["Period"] = "Pre-COVID"
pre_covid_plot = pre_covid_plot.rename(columns={"pre_covid_percent": "Percentage"})

post_covid_plot = post_summary[["full_category_clean", "post_covid_percent"]].copy()
post_covid_plot["Period"] = "Post-COVID"
post_covid_plot = post_covid_plot.rename(columns={"post_covid_percent": "Percentage"})

# Combine the two
plot_df = pd.concat([pre_covid_plot, post_covid_plot], axis=0)

# Step 2: Plot
plt.figure(figsize=(14, 6))
sns.barplot(
    data=plot_df,
    x="full_category_clean",
    y="Percentage",
    hue="Period",
    palette="Set2"  # or "pastel", "Set1", etc.
)
plt.xticks(rotation=90)
plt.ylabel("Percentage (%)")
plt.title("Fixed-route rider profile: Pre-COVID vs Post-COVID on Late Routes")
plt.axhline(0, color="gray", ls="--")
plt.legend(title="Survey Period")
plt.tight_layout()
plt.show()

