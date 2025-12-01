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
    """
    Function that removes any sensors from the given GeoDataFrame that do not have the broker name(s) provided.

    Returns a GeoPandas GeoDataFrame.
    """
    
    if isinstance(broker_names, str):
        broker_names = [broker_names]
    
    return gdf[gdf["Broker_Name"].isin(broker_names)]

def find_closest_sensors(gdf: gpd.GeoDataFrame, point: Point, broker_name: str, n: int) -> list[str]:
    """
    Function that finds n closest sensors to a given point.

    Returns a list of sensor names, in ascending order of distance from the point.
    """
    #As with other functions, creates a copy of the original data to avoid unintentionally mutating it.
    gdf = gdf.copy()
    gdf = filter_by_broker_name(gdf, broker_name)

    fixed_point = gpd.GeoSeries([point], crs=gdf.crs).to_crs("EPSG:27700")[0]

    #Transform from lat/long projection to one in meters so a distance can be calculated.
    gdf.to_crs("EPSG:27700", inplace=True)

    gdf["Distance"] = gdf.geometry.distance(fixed_point)
    gdf.sort_values("Distance", inplace=True)

    #Appends the first n sorted location names to a list.
    l = []
    for sensor in gdf["Sensor_Name"][0:n]:
        l.append(sensor)
    
    return l

def resample_sensors_timeseries(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """
    Function that resamples a timeseries to a given frequency.

    Returns a Pandas DataFrame of data resampled to frequency.
    """
    #Group the dataframe by variables that should be resampled with each other, ie each variable of each sensor.
    grouped = df.groupby(["Sensor_Name", "Variable"]).resample(freq)
    
    #Tell resample how to combine values in different columns.
    resampled_data = grouped.agg({
        "Value": "mean",
        "Flagged": "max"
    })

    #Remove N/A values to avoid getting N/A resampled values
    resampled_data = resampled_data.dropna(subset=["Value"])

    #Reset the index
    df = resampled_data.reset_index(level=["Sensor_Name", "Variable"])

    #Keep columns that were originall there.
    df = df[["Sensor_Name", "Variable", "Value", "Flagged"]]
    
    #Ensure dataframe is sorted from earliest timestamp
    df = df.sort_index()

    return df

def get_road_geometries(wkt_df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Function that finds the shortest road route between two points in a multiline WKT used for traffic sensors in the UO API.

    Returns a GeoPandas GeoDataFrame of the geometries of the shortest route between the points.
    """
    #Load a street network graph for newcastle.
    graph = ox.graph_from_place("Newcastle upon Tyne, UK", network_type="drive")
    graph_proj = ox.project_graph(graph)
    
    #Convert the WKT into geopandas geometry.
    gSeries = gpd.GeoSeries.from_wkt(wkt_df["Location_WKT"])
    
    final_geometries = []

    #Loops through the pairs of points and "draws" a route between them using the nodes on the graph.
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

        #If this fails, draw a straight line as the bird flies.    
        except (nx.NetworkXNoPath, ValueError):
            print(f"Routing failed, keeping original straight line.")
            final_geometries.append(geometry)

    #Create the final geodataframe with the projection the rest of the code uses.
    gdf = gpd.GeoDataFrame(wkt_df, geometry=final_geometries, crs="EPSG:4326")

    #Calculate the legnth of the routes.
    gdf["road_length(m)"] = gdf.to_crs(gdf.estimate_utm_crs()).length
    
    return gdf

def clip_timeseries_by_variable(df: pd.DataFrame, variables: Union[str, List[str]]) -> pd.DataFrame:
    """
    Function that removes any sensors from the given DataFrame that do not have the variable(s) provided.

    Returns a Pandas DataFrame.
    """
    
    if isinstance(variables, str):
        variables = [variables]

    return df[df["Variable"].isin(variables)]

def convert_long_df_to_wide(long_df: pd.DataFrame) -> pd.DataFrame:
    """
    Function that converts long datafrane with each reading on a new row into a wide dataframe with common timestamps on each row.
    
    Returns a Pandas DataFrame.
    """
    
    long_df = long_df.copy()

    long_df = long_df.reset_index()
    #Create a column name by combining the sensor name with the variable
    long_df["Column_Name"] = long_df["Sensor_Name"] + "_" + long_df["Variable"]

    #Construct the wide datframe with the column names
    wide_df = long_df.pivot(index = "Timestamp", columns= "Column_Name", values= "Value")

    return wide_df

def create_correlation_matrix(wide_df: pd.DataFrame) -> pd.DataFrame:
    """
    Function that performs correlation analysis on a wide dataframe of sensors and variables, made specifically to compare air quality and congestion.

    Removes any data where an average wind speed of 3m/s is recorded, as this will skew correlation.

    Returns a Pandas correlation DataFrame. 
    """
    wind_columns = wide_df.filter(like="Wind Speed")
    time_step_mean_wind  = wind_columns.mean(axis=1)
    return wide_df[time_step_mean_wind < 3].corr()

def clean_data(df: pd.DataFrame, freq: str, max_gap: int=24) -> pd.DataFrame:
    """
    Function that cleans dataframe of outliers and missing values.

    Returns a Pandas DataFrame.
    """
    df = df.copy()

    #Remove any negative values from the data as these are not valid.
    negatives_mask = df < 0
    negatives_count = negatives_mask.sum().sum()
    df[negatives_mask] = np.nan
    print(f"Negative value filtering removed {negatives_count} values.")

    #Calculate outliers using interquartile range as standard deviation is too skewed by outliers.
    Q1 = df.quantile(0.25)
    Q3 = df.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 3.0 * IQR
    upper_bound = Q3 + 3.0 * IQR

    outlier_mask = (df < lower_bound) | (df > upper_bound)
    outliers_count = outlier_mask.sum().sum()

    df[outlier_mask] = np.nan

    print(f"Outlier detection removed {outliers_count} values.")

    #Interpolate missing values over small gaps, but for signifcant gaps leave as NaN.
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
    """
    Function that reads CSV files of archieved UO data, so API call doesn't need to be made every time script is run.

    Returns a Pandas DataFrame
    """
    
    #This function was made as the length of data analysed in the report would take weeks at the rate the api responds to requests.
    #This could likely be solved with parrallellisation or a more customised requester, but this was beyond the scope of this assignment.
    df = pd.read_csv(filepath, index_col="Timestamp")
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={"Sensor Name" : "Sensor_Name"})
    df["Flagged"] = False

    if len(sensors) != 0:
        df = df[df["Sensor_Name"].isin(sensors)]

    return df

def decompose_timeseries(index: pd.Index, data: pd.Series) -> pd.DataFrame:
    """
    Function that decomposes a timseries into daily, weekly and monthly trends.

    Returns a Pandas DataFrame with the decomposition results.
    """
    
    data = data.interpolate(method="linear")
    
    #Use multi samplerate decomposer
    mstl = MSTL(data, periods=[24, 168, 730])
    res =  mstl.fit()

    trend = res.trend
    seasonal = res.seasonal
    resid = res.resid

    #Make columns more readable, for use when plotting.
    name_map = {
        "seasonal_24" : "Daily",
        "seasonal_168" : "Weekly",
        "seasonal_730" : "Monthly",
        "seasonal_8760" : "Yearly"
    }

    seasonal.rename(columns=name_map, inplace=True)

    results_df = pd.concat([data.rename("Original"), trend, seasonal, resid], axis=1)

    return results_df

def get_valid_scenario_dates(df: pd.DataFrame, variable_suffix: str):
    """
    Function that finds valid times to show rush hour air quality data, using rush hour and normal times obtained from decomposition analysis.

    Returns a datetime object.
    """

    #Get relevant colums based on variable required
    relevant_cols = [c for c in df.columns if c.endswith(variable_suffix)]

    if not relevant_cols:
        raise Exception(f"No columns found with suffix {variable_suffix}")

    #Use first value to check if not NaN
    check_col = relevant_cols[0]

    #Finds data at rush hour on a thursday
    thurs_data = df[(df.index.dayofweek == 3) & (df.index.hour == 17)]
    valid_thurs = thurs_data.dropna(subset=[check_col])

    if valid_thurs.empty:
        raise Exception("No valid data found for any Thursday at 17:00")

    worst_case_date = valid_thurs[check_col].idxmax().to_pydatetime()

    #Finds data after rush hour on a monday
    mon_data = df[(df.index.dayofweek == 0) & (df.index.hour == 10)]
    valid_mon = mon_data.dropna(subset=[check_col])

    if valid_mon.empty:
        raise Exception("No valid data found for any Monday at 10:00")

    comparison_date = valid_mon.index[0].to_pydatetime()

    return worst_case_date, comparison_date