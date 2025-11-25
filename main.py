import datetime

import pandas as pd
import geopandas as gpd

from shapely.geometry import Point

from uo_api_interface import *
from opg_api_interface import *
from data_analysis import *
from data_visualisation import *


def main():
    new_building_location = Point((-1.6260, 54.9816))

    gdf = get_sensor_locations()

    newcastle_boundry = get_boundry_of_location("Newcastle upon Tyne")[["geometry"]]

    gdf = gdf.sjoin(newcastle_boundry, "inner")
    gdf.drop(columns=["index_right"], inplace=True)

    gdf = classify_sensor_locations(gdf)

    key_sensor_types = ["People", "Air Quality", "Vehicles"]

    gdf = filter_by_sensor_type(gdf, key_sensor_types)

    three_closest_air_quality = find_closest_sensors(gdf, new_building_location, "Air Quality", 15)
    three_closest_vehicles = find_closest_sensors(gdf, new_building_location, "Vehicles", 5)

    print(three_closest_air_quality,"\n",three_closest_vehicles)

    fig0 = plot_sensor_locations(gdf)

    fig0.show()

    sensor_list = ["PER_TTN_AIRQUALITY012", "PER_NE_CAJT_NCA167_NBS1_CG", "PER_NE_CAJT_NCA167_CG_NBS1"]

    start = datetime.datetime(2025,5,5)
    end = datetime.datetime.now()
    multiple_timeseries = get_sensors_timeseries(sensor_list, start, end)
    multiple_timeseries = resample_sensors_timeseries(multiple_timeseries, "1d")
    print(multiple_timeseries["Variable"].unique())
    fig1 = plot_sensor_timseries(multiple_timeseries, "Journey Time")
    fig2 = plot_sensor_timseries(multiple_timeseries, "PM2.5")
    fig1.show()
    fig2.show()


if __name__ == "__main__":
    main()
