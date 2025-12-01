import requests
import datetime

import geopandas as gpd
import pandas as pd


def get_sensor_locations() -> gpd.GeoDataFrame:
    """
    Function that gets a full list of sensor locations from the urban observatory API.

    Returns a GeoPandas GeoDataFrame of sensor names and locations.
    """
    #Send request to UO API, limit disabled.
    response = requests.get(
        "https://api.v2.urbanobservatory.ac.uk/sensors/json", {"limit": -1}
    )
    if response.ok:
        #Turn JSON into a python usable format.
        data = response.json()
        #Construct dataframe.
        df = pd.DataFrame(data["Sensors"])
        #Transform into spatially efficient geodataframe.
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                df["Sensor_Centroid_Longitude"], df["Sensor_Centroid_Latitude"]
            ),
            crs="EPSG:4326",
        )
        #Drop unwanted columns.
        gdf.drop(
            columns=[
                "Sensor_Centroid_Longitude",
                "Sensor_Centroid_Latitude",
                "Location_WKT",
                "Ground_Height_Above_Sea_Level",
                "Sensor_Height_Above_Ground",
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

    Returns a Pandas DataFrame of sensor names and WKT onjects.
    """
    #Send request to UO API, limit disabled.
    response = requests.get(
        "https://api.v2.urbanobservatory.ac.uk/sensors/json", {"limit": -1}
    )
    if response.ok:
        #Turn JSON into a python usable format.
        data = response.json()
        #Construct dataframe.
        df = pd.DataFrame(data["Sensors"])
        #Drop unwanted columns.
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

    Returns a Pandas DataFrame of sensor data.
    """

    #Set params, this time using a limit to help prevent failed requests for large amounts of data.
    base_url = f"https://api.v2.urbanobservatory.ac.uk/sensors/{sensor_name}/data/json"
    limit = 1000
    offset = 0
    all_readings = []

    #Loop until there is no more "pages" of data for the given time period.
    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "start": start_datetime,
            "end": end_datetime
        }

        response = requests.get(base_url, params=params)

        if not response.ok:
            raise ValueError(f"Bad HTTP Response: Status Code {response.status_code}")

        data = response.json()
        readings = data.get("Readings", [])

        if not readings:
            break

        all_readings.extend(readings)

        if len(readings) < limit:
            break

        offset += limit

    if not all_readings:
        return pd.DataFrame()

    df = pd.DataFrame(all_readings)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df.set_index("Timestamp", inplace=True)
    return df
    
def get_sensor_timeseries_start(sensor_name: str) -> datetime.datetime:
    """
    Function that retrieves the start of a sensor's timeseries.

    Returns a datetime object.
    """
    #Requests a single line of data with a start param set long in the past.
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
    """
    Function that retrieves the end of a sensor's timeseries.

    Returns a datetime object.
    """    
    #Makes default requets to a sensor and gets the latest line of data.
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
    """
    Function that retrieves and concats data for multiple sensors for a given time period.

    Returns a Pandas DataFrame of requested data.
    """    
    
    #Create list of dataframes
    df_list = []
    failed_sensors = []

    #Loop through sensors using existing functions
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
        
    #Stitch list of dataframes together
    if len(df_list) != 0:    
        concatenated_df = pd.concat(df_list, ignore_index=False)

        concatenated_df.sort_index(inplace=True)

        return concatenated_df
    else:
        raise Exception("Error fetching data")