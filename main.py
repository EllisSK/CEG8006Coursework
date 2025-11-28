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

    all_sensors = get_sensor_locations()
    sensors_within_newcastle = all_sensors.sjoin(newcastle_boundry, "inner").drop(columns=["index_right"])

    sensors_to_use = ["NE Travel Data API", "aq_mesh_api"]

    relevant_sensors = filter_by_broker_name(sensors_within_newcastle, sensors_to_use)

    fig = create_all_sensors_within_boundary_plot(relevant_sensors, newcastle_boundry)
    save_figure(fig, "all_sensors_within_boundary")

    air_quality_sensors = find_closest_sensors(relevant_sensors, new_building_location, "aq_mesh_api", 50)
    vehicle_sensors = find_closest_sensors(relevant_sensors, new_building_location, "NE Travel Data API", 20)

    roads = get_sensors_wkt(vehicle_sensors)
    road_geometries = get_road_geometries(roads)

    fig = create_road_link_plot(road_geometries)
    save_figure(fig, "traffic_routes")

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
