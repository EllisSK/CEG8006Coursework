import datetime

import pandas as pd
import geopandas as gpd

from shapely.geometry import Point

from uo_api_interface import *
from opg_api_interface import *
from data_analysis import *
from data_visualisation import *


def main():
    new_building_location = Point((-1.625129, 54.981496))
    newcastle_boundry = get_boundry_of_location("Newcastle upon Tyne")[["geometry"]]

    all_sensors = get_sensor_locations()
    sensors_within_newcastle = all_sensors.sjoin(newcastle_boundry, "inner").drop(columns=["index_right"])

    sensors_to_use = ["NE Travel Data API", "aq_mesh_api"]

    relevant_sensors = filter_by_broker_name(sensors_within_newcastle, sensors_to_use)

    fig = create_all_sensors_within_boundary_plot(relevant_sensors, newcastle_boundry)
    save_figure(fig, "all_sensors_within_boundary")

    air_quality_sensors = find_closest_sensors(relevant_sensors, new_building_location, "aq_mesh_api", 30)
    air_quality_sensor_locations = relevant_sensors[relevant_sensors["Sensor_Name"].isin(air_quality_sensors)]

    fig = create_air_quality_sensor_location_plot(air_quality_sensor_locations)
    save_figure(fig, "air_quality_sensors")

    vehicle_sensors = find_closest_sensors(relevant_sensors, new_building_location, "NE Travel Data API", 20)

    roads = get_sensors_wkt(vehicle_sensors)
    road_geometries = get_road_geometries(roads)

    fig = create_road_link_plot(road_geometries)
    save_figure(fig, "traffic_routes")

    fig = create_air_quality_road_links_site_location_plot(air_quality_sensor_locations, road_geometries, new_building_location)
    save_figure(fig, "sensors_roads_building")

    data_start = datetime.datetime(2023,5,5)
    data_end = datetime.datetime.now()

    air_quality_timeseries = import_archive_dataset(Path("outputs/data/air.csv"), air_quality_sensors)

    traffic_timeseries = import_archive_dataset(Path("outputs/data/traffic.csv"), vehicle_sensors)
    
    air_quality_timeseries = resample_sensors_timeseries(air_quality_timeseries, "1h")
    traffic_timeseries = resample_sensors_timeseries(traffic_timeseries, "1h")

    air_quality_timeseries = convert_long_df_to_wide(air_quality_timeseries)[data_start:data_end]
    traffic_timeseries = convert_long_df_to_wide(traffic_timeseries)[data_start:data_end]

    combined_df = pd.concat([air_quality_timeseries, traffic_timeseries], axis=1)
    combined_df = clean_data(combined_df, "1h")
    corr_df = create_correlation_matrix(combined_df)
    
    fig = create_correlation_heatmap(corr_df)
    save_figure(fig, "corr_heatmap")

    decomposed_timeseries = decompose_timeseries(traffic_timeseries.index, traffic_timeseries[f"{vehicle_sensors[0]}_Journey Time"])
    
    fig = create_decomposed_trend_plot(decomposed_timeseries)
    save_figure(fig, "decomposed_trend")

    fig = create_decomposed_timeseries_plot(decomposed_timeseries)
    save_figure(fig, "decomposed_timeseries")

if __name__ == "__main__":
    main()
