import datetime

import pandas as pd
import geopandas as gpd

from shapely.geometry import Point

from uo_api_interface import *
from opg_api_interface import *
from data_analysis import *
from data_visualisation import *


def main():
    new_building_location = Point((-1.6260, 54.9816)) #Update this
    newcastle_boundry = get_boundry_of_location("Newcastle upon Tyne")[["geometry"]]

    gdf = get_sensor_locations()

    gdf = gdf.sjoin(newcastle_boundry, "inner").drop(columns=["index_right"])

    sensors_to_use = ["NE Travel Data API", "aq_mesh_api"]

    gdf = filter_by_broker_name(gdf, sensors_to_use)

    closest_air_quality = find_closest_sensors(gdf, new_building_location, "aq_mesh_api", 50)
    closest_vehicle = find_closest_sensors(gdf, new_building_location, "NE Travel Data API", 20)

    roads = get_sensors_wkt(closest_vehicle)
    road_geometries = get_road_geometries(roads)
    print(newcastle_boundry)

    fig = create_all_sensors_within_boundary_plot(gdf, newcastle_boundry)

    fig.show()

    """
    start = datetime.datetime(2025,5,5)
    end = datetime.datetime.now()
    multiple_timeseries = get_sensors_timeseries(sensor_list, start, end)
    multiple_timeseries = resample_sensors_timeseries(multiple_timeseries, "1d")
    print(multiple_timeseries["Variable"].unique())
    fig1 = plot_sensor_timseries(multiple_timeseries, "Journey Time")
    fig2 = plot_sensor_timseries(multiple_timeseries, "PM2.5")
    fig1.show()
    fig2.show()
    """


if __name__ == "__main__":
    main()
