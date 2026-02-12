import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math
import os

MARKS_FILE = "map.csv"
LINES_FILE = "saved_lines.csv"


# ----------------------------
# Distance NM
# ----------------------------
def haversine_nm(lat1, lon1, lat2, lon2):
    R_km = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    km = R_km * c
    return km / 1.852


# ----------------------------
# Load Marks
# ----------------------------
df = pd.read_csv(MARKS_FILE)
df = df.dropna(subset=["Lat", "Long"])
df = df[["Mark Name", "Description", "Light", "Lat", "Long"]]


# ----------------------------
# Load Saved Lines
# ----------------------------
if os.path.exists(LINES_FILE):
    lines_df = pd.read_csv(LINES_FILE)

    # Add Color column if missing
    if "Color" not in lines_df.columns:
        lines_df["Color"] = "black"
        lines_df.to_csv(LINES_FILE, index=False)

else:
    lines_df = pd.DataFrame(columns=["StartMark", "EndMark", "DistanceNM", "Color"])

# ----------------------------
# Highlight Special Legs
# ----------------------------
special_legs = [
    ("R 4", "R3"),
    ("R 4", "X-Ray"),
]

for start, end in special_legs:
    mask = (lines_df["StartMark"] == start) & (lines_df["EndMark"] == end)
    lines_df.loc[mask, "Color"] = "red"

# Save updates
lines_df.to_csv(LINES_FILE, index=False)


# ----------------------------
# Session State for Clicks
# ----------------------------
if "clicked_marks" not in st.session_state:
    st.session_state.clicked_marks = []

# ----------------------------
# UI
# ----------------------------
st.set_page_config(layout="wide")
st.title("Navigators Challenge Course")
st.write("Click on marks to view mark names, click on lines to view distances. Red legs are manditory legs of the course, the longest red one  being the the St.Leonards race itself")
# ----------------------------
# Create Map
# ----------------------------
m = folium.Map(
    location=[df["Lat"].mean(), df["Long"].mean()],
    zoom_start=10.4,
    tiles="OpenStreetMap",
    control_scale=True,
    zoom_control=True
)

m.scrollWheelZoom = True


# Nautical Overlay
folium.TileLayer(
    tiles="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
    attr="© OpenSeaMap contributors",
    name="Seamarks",
    overlay=True
).add_to(m)

# ----------------------------
# Add Marks (Clickable)
# ----------------------------
for _, row in df.iterrows():
    popup_text = f"""
        <div style="
        font-size:12pt;
        font-family:Arial;
        ">
        <b>{row['Mark Name']}</b><br><br>
        <b>Description:</b> {row['Description']}<br>
        <b>Light:</b> {row['Light']}<br>
        <b>Position:</b> {row['Lat']:.4f}, {row['Long']:.4f}
        </div>
        """

    folium.CircleMarker(
    location=[row["Lat"], row["Long"]],
    radius=6,
    color="yellow",
    fill=True,
    fill_opacity=1,
    popup=folium.Popup(popup_text, max_width=300),
    tooltip=row["Mark Name"]
).add_to(m)


# ----------------------------
# Draw Saved Lines
# ----------------------------
for _, row in lines_df.iterrows():
    start = df[df["Mark Name"] == row["StartMark"]].iloc[0]
    end = df[df["Mark Name"] == row["EndMark"]].iloc[0]

    folium.PolyLine(
    locations=[
        (start["Lat"], start["Long"]),
        (end["Lat"], end["Long"])
    ],
    color=row["Color"],   # ✅ Use CSV value
    weight=3,
    tooltip=f"{row['StartMark']} → {row['EndMark']} ({row['DistanceNM']:.2f} NM)"
).add_to(m)



# ----------------------------
# Show Map + Capture Click
# ----------------------------
map_data = st_folium(m, height=900, use_container_width=True)

# ----------------------------
# Table
# ----------------------------
st.subheader("📌 Saved Legs")
st.dataframe(lines_df)
