import datetime

import pandas as pd
import geopandas as gpd
import numpy as np


def classify_sensor_locations(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    sensor_strings = [
        gdf["Sensor_Name"].str.startswith(("PER_TTN", "PER_AIRMON")),
        gdf["Sensor_Name"].str.startswith("PER_PEOPLE"),
        gdf["Sensor_Name"].str.startswith("PER_NE_CAJT"),
        gdf["Sensor_Name"].str.startswith(("PER_BUILDING", "PER_INTERNAL_BUILDING")),
    ]

    classes = ["Air Quality", "People", "Vehicles", "Building"]

    gdf["Sensor_Type"] = np.select(sensor_strings, classes, default="Other")

    return gdf

def resample_sensors_timeseries(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    grouped = df.groupby(["Sensor_Name", "Variable"]).resample(freq)
    
    resampled_data = grouped.agg({
        "Value": "mean",
        "Flagged": "max"
    })

    resampled_data = resampled_data.dropna(subset=["Value"])

    df = resampled_data.reset_index(level=["Sensor_Name", "Variable"])

    df = df[["Sensor_Name", "Variable", "Value", "Flagged"]]
    
    df = df.sort_index()

    return df

def decompose_timeseries():
    pass