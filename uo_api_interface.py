import requests
import datetime

import geopandas as gpd
import pandas as pd


def get_sensor_locations() -> gpd.GeoDataFrame:
    """
    Function that gets a full list of sensor locations from the urban observatory API.
    """
    response = requests.get(
        "https://api.v2.urbanobservatory.ac.uk/sensors/json", {"limit": -1}
    )
    if response.ok:
        data = response.json()
        df = pd.DataFrame(data["Sensors"])
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                df["Sensor_Centroid_Longitude"], df["Sensor_Centroid_Latitude"]
            ),
            crs="EPSG:4326",
        )
        gdf.drop(
            columns=[
                "Sensor_Centroid_Longitude",
                "Sensor_Centroid_Latitude",
                "Location_WKT",
                "Ground_Height_Above_Sea_Level",
                "Sensor_Height_Above_Ground",
                "Broker_Name",
                "Raw_ID",
            ],
            inplace=True,
        )
        return gdf
    else:
        raise ValueError(f"Bad HTTP Response: Status Code {response.status_code}")


def get_sensor_timeseries(
    sensor_name: str, start_datetime: datetime.datetime, end_datetime: datetime.datetime
) -> pd.DataFrame:
    """
    Function that gets a timeseries of sensor data from a given sensor on the urban observatory API between two datetimes.

    sensor_name: Name of the sensor in the urban observatory API.

    start_datetime: Datetime object the timeseries should start from.

    end_datetime: Datetime object the timeseries should end at.
    """

    p = {"limit": -1, "start": start_datetime, "end": end_datetime}
    response = requests.get(
        f"https://api.v2.urbanobservatory.ac.uk/sensors/{sensor_name}/data/json", p
    )
    if response.ok:
        data = response.json()
        df = pd.DataFrame(data["Readings"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df.set_index("Timestamp", inplace=True)
        return df
    else:
        raise ValueError("Bad HTTP Response")
    
def get_sensor_timeseries_start(sensor_name: str) -> datetime.datetime:
    p = {"limit": 1, "start": datetime.datetime(1970,1,1), "end": datetime.datetime.now()}
    response = requests.get(
        f"https://api.v2.urbanobservatory.ac.uk/sensors/{sensor_name}/data/json", p
    )
    if response.ok:
        data = response.json()
        df = pd.DataFrame(data["Readings"])
        timestamp_str = df.iloc[0]["Timestamp"]
        return pd.to_datetime(timestamp_str)
    else:
        raise ValueError("Bad HTTP Response")

def get_sensor_timeseries_end(sensor_name: str) -> datetime.datetime:
    response = requests.get(
        f"https://api.v2.urbanobservatory.ac.uk/sensors/{sensor_name}/data/json"
    )
    if response.ok:
        data = response.json()
        df = pd.DataFrame(data["Readings"])
        timestamp_str = df.iloc[-1]["Timestamp"]
        return pd.to_datetime(timestamp_str)
    else:
        raise ValueError("Bad HTTP Response")
    
def get_sensors_timeseries(sensors: list[str], sensor_gdf: gpd.GeoDataFrame, start_datetime: datetime.datetime, end_datetime: datetime.datetime) -> gpd.GeoDataFrame:
    master_gdf = gpd.GeoDataFrame(columns=["Sensor_Name", "Sensor_Location", "Timestamp", "Value"])
    master_gdf.set_index("Timestamp", inplace=True)
    
    sensor_gdf = sensor_gdf.copy()
    gdf_list = []
    sensor_gdf = sensor_gdf.set_index("Sensor_Name")

    for sensor in sensors:
        location = sensor_gdf.loc[sensor, "geometry"]
        timeseries = get_sensor_timeseries(sensor, start_datetime, end_datetime)
        
        if timeseries.empty:
            continue
        
        timeseries.reset_index(inplace=True)
        timeseries["Timestamp"] = pd.to_datetime(timeseries["Timestamp"])
        timeseries["geometry"] = location

        current_gdf = gpd.GeoDataFrame(
            timeseries, 
            geometry="geometry", 
            crs="EPSG:4326"
        )

        current_gdf["Sensor_Name"] = sensor

        current_gdf.set_index("Timestamp", inplace=True)
        
        gdf_list.append(current_gdf)
        
    if len(gdf_list) != 0:    
        concatenated_df = pd.concat(gdf_list, ignore_index=False)

        master_gdf = gpd.GeoDataFrame(concatenated_df, geometry="geometry", crs="EPSG:4326")

    master_gdf.sort_index(inplace=True)

    return master_gdf
