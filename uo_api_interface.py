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
        return df
    else:
        raise ValueError("Bad HTTP Response")
