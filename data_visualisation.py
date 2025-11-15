import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

def plot_sensor_locations(gdf: gpd.GeoDataFrame) -> go.Figure:
    gdf = gdf.copy()

    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    fig = px.scatter_map(
        gdf,
        lat="lat",
        lon="lon",
        hover_name="Sensor_Name"
    )

    
    return fig

def create_air_polution_heatmap():
    pass