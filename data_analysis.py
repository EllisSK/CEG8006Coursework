import pandas as pd
import geopandas as gpd
import numpy as np

def classify_sensor_locations(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    sensor_strings = [
    gdf["Sensor_Name"].str.startswith(("PER_TTN", "PER_AIRMON")),
    gdf["Sensor_Name"].str.startswith("PER_PEOPLE"),
    gdf["Sensor_Name"].str.startswith("PER_NE_CAJT"),
    gdf["Sensor_Name"].str.startswith(("PER_BUILDING", "PER_INTERNAL_BUILDING"))
    ]

    classes = [
    "Air Quality",
    "People",
    "Vehicles",
    "Building"
    ]

    gdf["Sensor_Type"] = np.select(sensor_strings, classes, default="Other")

    return gdf