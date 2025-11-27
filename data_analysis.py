import datetime

import pandas as pd
import geopandas as gpd
import numpy as np
import osmnx as ox
import networkx as nx

from shapely.geometry import Point
from shapely.ops import unary_union
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

def create_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    
    return pd.DataFrame()

def decompose_timeseries():
    pass