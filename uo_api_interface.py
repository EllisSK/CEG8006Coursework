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
    
def get_sensors_wkt(sensor_list: list) -> pd.DataFrame:
    """
    Function that gets a list of sensor WKTs from the urban observatory API.
    """
    response = requests.get(
        "https://api.v2.urbanobservatory.ac.uk/sensors/json", {"limit": -1}
    )
    if response.ok:
        data = response.json()
        df = pd.DataFrame(data["Sensors"])
        df.drop(
            columns=[
                "Sensor_Centroid_Longitude",
                "Sensor_Centroid_Latitude",
                "Ground_Height_Above_Sea_Level",
                "Sensor_Height_Above_Ground",
                "Broker_Name",
                "Raw_ID",
            ],
            inplace=True
            )
        return df[df["Sensor_Name"].isin(sensor_list)]

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
    
def get_sensors_timeseries(sensors: list[str], start_datetime: datetime.datetime, end_datetime: datetime.datetime) -> pd.DataFrame:
    master_df = pd.DataFrame(columns=["Sensor_Name", "Sensor_Location", "Timestamp", "Value"])
    master_df.set_index("Timestamp", inplace=True)
    
    df_list = []
    failed_sensors = []

    for sensor in sensors:
        try:
            timeseries = get_sensor_timeseries(sensor, start_datetime, end_datetime)
        except:
            failed_sensors.append(sensor)
            continue
        
        if timeseries.empty:
            continue
        
        timeseries.reset_index(inplace=True)
        timeseries["Timestamp"] = pd.to_datetime(timeseries["Timestamp"])

        current_df = timeseries

        current_df["Sensor_Name"] = sensor

        current_df.set_index("Timestamp", inplace=True)
        
        df_list.append(current_df)
        
    if len(df_list) != 0:    
        concatenated_df = pd.concat(df_list, ignore_index=False)

        concatenated_df.sort_index(inplace=True)

        return concatenated_df
    else:
        raise Exception("Error fetching data")