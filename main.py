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

    gdf = gdf[gdf["Sensor_Type"].isin(("People", "Air Quality", "Vehicles"))]

    gdf.loc[len(gdf)] = ["Moorview Green",new_building_location,"New Building"]

    fig0 = plot_sensor_locations(gdf)

    fig0.show()


if __name__ == "__main__":
    main()
