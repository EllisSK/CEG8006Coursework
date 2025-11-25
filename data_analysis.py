import datetime

import pandas as pd
import geopandas as gpd
import numpy as np

from shapely.geometry import Point
from typing import Union, List


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

def filter_by_sensor_type(gdf: gpd.GeoDataFrame, sensor_types: Union[str, List[str]]) -> gpd.GeoDataFrame:
    if isinstance(sensor_types, str):
        sensor_types = [sensor_types]
    
    return gdf[gdf["Sensor_Type"].isin(sensor_types)]

def find_closest_sensors(gdf: gpd.GeoDataFrame, point: Point, sensor_type: str, n: int) -> list[str]:
    gdf = gdf.copy()
    gdf = filter_by_sensor_type(gdf, sensor_type)

    fixed_point = gpd.GeoSeries([point], crs=gdf.crs).to_crs("EPSG:27700")[0]

    gdf.to_crs("EPSG:27700", inplace=True)

    gdf["Distance"] = gdf.geometry.distance(fixed_point)
    gdf.sort_values("Distance", inplace=True)

    l = []
    for sensor in gdf["Sensor_Name"][0:n+1]:
        l.append(sensor)
    
    return l

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

def create_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    
    return pd.DataFrame()

def decompose_timeseries():
    pass