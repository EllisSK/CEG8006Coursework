import pandas as pd
import geopandas as gpd

from shapely.geometry import Point

from ou_api_interface import *
from os_api_interface import *
from data_analysis import *
from data_visualisation import *


def main():
    new_building_location = Point((54.9816, -1.6260))

    gdf = get_sensor_locations()

    print(gdf.head)


if __name__ == "__main__":
    main()
