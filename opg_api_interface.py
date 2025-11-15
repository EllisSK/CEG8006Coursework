import requests

import geopandas as gpd


def get_boundry_of_location(location: str) -> gpd.GeoDataFrame:
    url = f" https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_December_2023_Boundaries_UK_BGC/FeatureServer/0/query"

    p = {"where": location, "outFields": "*", "outSR": "4326", "f": "geojson"}

    response = requests.get(url, p)

    if response.ok:
        data = response.json()
        gdf = gpd.GeoDataFrame.from_features(data["features"])
        gdf.set_crs(epsg=4326, inplace=True)
        return gdf
    else:
        raise ValueError("Bad HTTP Response")
