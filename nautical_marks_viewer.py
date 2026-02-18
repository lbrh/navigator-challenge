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

# Add numbering (1, 2, 3...)
df = df.reset_index(drop=True)
df["Mark Number"] = df.index + 1


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
# UI
# ----------------------------
st.set_page_config(layout="wide")

st.title("Navigators Challenge Course")

st.write(
    "Click on marks to view buoy details. "
    "Click on lines to view distances. "
    "Red legs are mandatory legs of the course."
)


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
        color=row["Color"],
        weight=3,
        tooltip=f"{row['StartMark']} → {row['EndMark']} ({row['DistanceNM']:.2f} NM)"
    ).add_to(m)


# ----------------------------
# Add Numbered Marks
# ----------------------------
for _, row in df.iterrows():

    popup_text = f"""
    <div style="font-size:12pt; font-family:Arial;">
        <b>Mark {row['Mark Number']}: {row['Mark Name']}</b><br><br>
        <b>Description:</b> {row['Description']}<br>
        <b>Light:</b> {row['Light']}<br>
        <b>Position:</b> {row['Lat']:.4f}, {row['Long']:.4f}
    </div>
    """

    # Buoy dot marker
    folium.CircleMarker(
        location=[row["Lat"], row["Long"]],
        radius=10,
        color="black",
        fill=True,
        fill_color="yellow",
        fill_opacity=1,
        popup=folium.Popup(popup_text, max_width=300),
        tooltip=f"{row['Mark Number']} - {row['Mark Name']}"
    ).add_to(m)

    # Number label on top
    folium.Marker(
        location=[row["Lat"], row["Long"]],
        icon=folium.DivIcon(
            html=f"""
            <div style="
                font-size:8pt;
                font-weight:bold;
                color:black;
                text-align:center;
                line-height:10px;
            ">
                {row['Mark Number']}
            </div>
            """
        )
    ).add_to(m)

# ----------------------------
# Show Map
# ----------------------------
map_data = st_folium(
    m,
    height=900,
    width='stretch'
)


# ----------------------------
# Mark Legend Table
# ----------------------------
st.subheader("📍 Mark Key (Number → Name)")

legend_df = df[["Mark Number", "Mark Name"]].rename(
    columns={
        "Mark Number": "#",
        "Mark Name": "Mark"
    }
)

st.dataframe(legend_df, width='stretch')

# ----------------------------
# Saved Legs Table
# ----------------------------
st.subheader("📌 Saved Legs")

st.dataframe(lines_df, width='stretch')

m.save("map.html")

