import sys
import folium

sys.path.append("/home/metivier/Nextcloud/src/GPS/")
from LibGPS import *

# Retrieve waypoints
filename = "../Data/c60x.gpx"
df = get_waypoints(filename)

# Create the map
macarte = folium.Map(location=[49.119777, 1.769824], zoom_start=19)
hybrid = folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    attr="Google",
    name="Google Satellite",
    overlay=True,
    control=True,
)
hybrid.add_to(macarte)

# Add markers

df.apply(
    lambda row: folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=10,
        color="red",
        popup=row["name"],
    ).add_to(macarte),
    axis=1,
)

macarte.save("vexin.html")
