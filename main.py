import datetime

import pandas as pd
import geopandas as gpd

from shapely.geometry import Point

from uo_api_interface import *
from opg_api_interface import *
from data_analysis import *
from data_visualisation import *


def main():
    new_building_location = Point((54.9816, -1.6260))

    gdf = get_sensor_locations()
    
    newcastle_boundry = get_boundry_of_location("LAD23NM = 'Newcastle upon Tyne'")

    gdf = gdf.sjoin(newcastle_boundry, "inner")

    gdf = classify_sensor_locations(gdf)

    fig0 = plot_sensor_locations(gdf)

    fig0.show()




if __name__ == "__main__":
    main()
