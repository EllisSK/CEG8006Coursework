import datetime

import pandas as pd
import geopandas as gpd
import numpy as np
import osmnx as ox
import networkx as nx

from shapely.geometry import Point
from shapely.ops import unary_union
from typing import Union, List
from pathlib import Path
from statsmodels.tsa.seasonal import MSTL

from uo_api_interface import *


def filter_by_broker_name(gdf: gpd.GeoDataFrame, broker_names: Union[str, List[str]]) -> gpd.GeoDataFrame:
    if isinstance(broker_names, str):
        broker_names = [broker_names]
    
    return gdf[gdf["Broker_Name"].isin(broker_names)]

def find_closest_sensors(gdf: gpd.GeoDataFrame, point: Point, broker_name: str, n: int) -> list[str]:
    gdf = gdf.copy()
    gdf = filter_by_broker_name(gdf, broker_name)

    fixed_point = gpd.GeoSeries([point], crs=gdf.crs).to_crs("EPSG:27700")[0]

    gdf.to_crs("EPSG:27700", inplace=True)

    gdf["Distance"] = gdf.geometry.distance(fixed_point)
    gdf.sort_values("Distance", inplace=True)

    l = []
    for sensor in gdf["Sensor_Name"][0:n]:
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

def get_road_geometries(wkt_df: pd.DataFrame) -> gpd.GeoDataFrame:
    graph = ox.graph_from_place("Newcastle upon Tyne, UK", network_type="drive")
    graph_proj = ox.project_graph(graph)
    
    gSeries = gpd.GeoSeries.from_wkt(wkt_df["Location_WKT"])
    
    final_geometries = []

    for geometry in gSeries:
        start_point = geometry.coords[0]
        end_point = geometry.coords[-1]

        orig_node = ox.nearest_nodes(graph, X=start_point[0], Y=start_point[1])
        dest_node = ox.nearest_nodes(graph, X=end_point[0], Y=end_point[1])

        try:
            route_nodes = nx.shortest_path(graph_proj, orig_node, dest_node, weight="length")
            
            route_gdf = ox.routing.route_to_gdf(graph_proj, route_nodes, weight="length")
            combined_line_proj = unary_union(route_gdf.geometry)
            
            combined_line_4326 = gpd.GeoSeries([combined_line_proj], crs=graph_proj.graph["crs"]).to_crs("EPSG:4326").iloc[0]
            
            final_geometries.append(combined_line_4326)
            
        except (nx.NetworkXNoPath, ValueError):
            print(f"Routing failed, keeping original straight line.")
            final_geometries.append(geometry)

    gdf = gpd.GeoDataFrame(wkt_df, geometry=final_geometries, crs="EPSG:4326")

    gdf["road_length(m)"] = gdf.to_crs(gdf.estimate_utm_crs()).length
    
    return gdf

def clip_timeseries_by_variable(df: pd.DataFrame, variables: Union[str, List[str]]) -> pd.DataFrame:
    if isinstance(variables, str):
        variables = [variables]

    return df[df["Variable"].isin(variables)]

def convert_long_df_to_wide(long_df: pd.DataFrame) -> pd.DataFrame:
    long_df = long_df.copy()

    long_df = long_df.reset_index()
    long_df["Column_Name"] = long_df["Sensor_Name"] + "_" + long_df["Variable"]

    wide_df = long_df.pivot(index = "Timestamp", columns= "Column_Name", values= "Value")

    return wide_df

def create_correlation_matrix(long_df: pd.DataFrame) -> pd.DataFrame:
    wind_columns = long_df.filter(like="Wind Speed")
    time_step_mean_wind  = wind_columns.mean(axis=1)
    return long_df[time_step_mean_wind < 3].corr()

def clean_data(df: pd.DataFrame, freq: str, max_gap: int=24) -> pd.DataFrame:
    df = df.copy()

    full_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
    df = df.reindex(full_idx)
    df.index.name = "Timestamp"
    original_nans = df.isna().sum().sum()
    df = df.interpolate(method="time", limit=max_gap, limit_direction="both")
    remaining_nans = df.isna().sum().sum()
    nans_removed = original_nans - remaining_nans
    print(f"Cleaning removed {nans_removed} NaN values, {remaining_nans} remain.")

    return df

def import_archive_dataset(filepath: Path, sensors: list = []) -> pd.DataFrame:
    df = pd.read_csv(filepath, index_col="Timestamp")
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={"Sensor Name" : "Sensor_Name"})
    df["Flagged"] = False

    if len(sensors) != 0:
        df = df[df["Sensor_Name"].isin(sensors)]

    return df

def decompose_timeseries(index: pd.Index, data: pd.Series):
    data = data.interpolate(method="linear")
    
    mstl = MSTL(data, periods=[24, 168, 730])
    res =  mstl.fit()

    trend = res.trend
    seasonal = res.seasonal
    resid = res.resid

    name_map = {
        "seasonal_24" : "Daily",
        "seasonal_168" : "Weekly",
        "seasonal_730" : "Monthly",
        "seasonal_8760" : "Yearly"
    }

    seasonal.rename(columns=name_map, inplace=True)

    results_df = pd.concat([data.rename("Original"), trend, seasonal, resid], axis=1)

    return results_df