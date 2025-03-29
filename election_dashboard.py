import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
import plotly.express as px

# -------------------------------
# Set Wide Layout
# -------------------------------
st.set_page_config(layout="wide", page_title="Election Data Analysis Dashboard")

# -------------------------------
# Load Data
# -------------------------------
@st.cache_data
def load_data():
    file_id = "1J07UzjwFU56aX918bv0pHfh_J8qDzg4T"  # Your Google Drive file ID
    url = f"https://drive.google.com/uc?id={file_id}"
    return pd.read_csv(url)

df = load_data()

# -------------------------------
# 1. Dashboard Title
# -------------------------------
st.title("🗳️ Election Data Analysis Dashboard")
st.markdown("""
This dashboard visualizes spatial-temporal anomalies, clustering patterns, and historical trends.  
It includes:
- **Geographic Clusters and Outliers Map**: Visualizes polling unit clusters and outliers.
- **Party Vote Distribution**: Compares vote shares and z‑scores for each party.
- **Neighborhood Comparisons**: Highlights differences across LGAs/Wards.
- **Historical Trends**: Shows how election results have evolved over time.
""")

# -------------------------------
# 2. KPI Metrics Overview
# -------------------------------
st.header("📊 Key Metrics Overview")

# Compute key stats
total_polling_units = df["PU-Code"].nunique()
total_votes = int(df["Total_Votes"].sum())
total_registered = df["Registered_Voters"].sum()
total_accredited = df["Accredited_Voters"].sum()
voter_turnout = (total_accredited / total_registered) * 100

# Create KPI containers
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="🏠 Total Polling Units", value=total_polling_units)

with col2:
    st.metric(label="🗳️ Total Votes Cast", value=f"{total_votes:,}")

with col3:
    st.metric(label="📋 Registered Voters", value=f"{total_registered:,}")

with col4:
    st.metric(label="✅ Accredited Voters", value=f"{total_accredited:,}")

with col5:
    st.metric(label="📊 Voter Turnout (%)", value=f"{voter_turnout:.2f}%")

# -------------------------------
# 3. Geographic Outlier Map (Using Folium)
# -------------------------------
st.header("📍 Geographic Clusters and Outliers Map")

# Create a base map centered on average location
map_center = [df['Latitude'].mean(), df['Longitude'].mean()]
m = folium.Map(location=map_center, zoom_start=10)

# Add MarkerCluster layer
marker_cluster = MarkerCluster().add_to(m)
for _, row in df.iterrows():
    popup_text = f"""
    <strong>PU-Name:</strong> {row['PU-Name']}<br>
    <strong>Cluster:</strong> {row['HDBSCAN_Cluster']}<br>
    <strong>Total Votes:</strong> {row['Total_Votes']}<br>
    <strong>Accredited Ratio:</strong> {row['Accredited_Ratio']:.2f}<br>
    <strong>Global Composite Score:</strong> {row['Global_Composite_Score']:.2f}
    """
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=row['color'], icon="cloud")
    ).add_to(marker_cluster)

# Heatmap Layer
heat_data = df[['Latitude', 'Longitude', 'Global_Composite_Score']].dropna().values.tolist()
HeatMap(heat_data, radius=12, blur=15, max_zoom=12).add_to(m)

# Display map
st_folium(m, width=1200, height=500)

# -------------------------------
# 4. Party Vote Distribution & Outlier Z-Scores
# -------------------------------
st.header("📊 Party Vote Distribution & Outlier Z-Scores")

# Top 5 Outlier Z-Scores
top_5_outliers = df.sort_values(by="Global_Composite_Score", ascending=False).head(5)

st.subheader("🔍 Top 5 Outlier Polling Units")
st.dataframe(top_5_outliers[[  
        "PU-Name", "Total_Votes", "Accredited_Voters", "Accredited_Ratio",
        "APC_z_score", "PDP_z_score", "LP_z_score", "NNPP_z_score",
        "Global_Composite_Score"
    ]])

st.subheader("📊 Party Z-Scores for Top 5 Outliers")
z_df = top_5_outliers.melt(
        id_vars="PU-Name", 
        value_vars=["APC_z_score", "PDP_z_score", "LP_z_score", "NNPP_z_score"],
        var_name="Party", 
        value_name="Z-Score"
    )
fig_z = px.bar(
        z_df, 
        x="PU-Name", 
        y="Z-Score", 
        color="Party", 
        title="Party-Specific Z-Scores for Top 5 Outliers",
        barmode="group"
    )
st.plotly_chart(fig_z, use_container_width=True)

# -------------------------------
# 5. Neighborhood Comparisons (LGA)
# -------------------------------
st.header("🏘️ Neighborhood Comparisons")

lga_comparison = df.groupby("LGA")["Global_Composite_Score"].mean().round(2).sort_values(ascending=False).reset_index()
fig_lga = px.bar(
    lga_comparison,
    x="LGA", y="Global_Composite_Score",
    title="Average Global Composite Score by LGA",
    text="Global_Composite_Score"
)
st.plotly_chart(fig_lga, use_container_width=True)

# -------------------------------
# 6. Historical Trends (2011 - 2023)
# -------------------------------
st.header("📈 Historical Election Trends (2011 - 2023)")

# Define historical election data (including 2023)
historical_election_data = pd.DataFrame({
    "Year": [2011, 2015, 2019, 2023],
    "APC": [None, 528620, 365229, df["APC"].sum()],  # 2023 data from the dataset
    "PDP": [484758, 303376, 366690, df["PDP"].sum()],
    "LP": [None, None, 360, df["LP"].sum()],
    "NNPP": [None, None, 430, df["NNPP"].sum()]
})

# Convert None to NaN for better visualization
historical_election_data.fillna(0, inplace=True)

# Create a line chart
fig_hist = px.line(
    historical_election_data,
    x="Year",
    y=["APC", "PDP", "LP", "NNPP"],
    title="Historical Election Results (2011 - 2023)",
    markers=True,
    labels={"value": "Total Votes", "variable": "Party"}
)

# Display chart
st.plotly_chart(fig_hist, use_container_width=True)
