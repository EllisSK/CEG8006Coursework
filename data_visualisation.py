import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go


def plot_sensor_locations(gdf: gpd.GeoDataFrame) -> go.Figure:
    gdf = gdf.copy()

    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    fig = px.scatter_map(
        gdf, lat="lat",
        lon="lon",
        hover_name="Sensor_Name",
        color="Sensor_Type",
        map_style="open-street-map",
        title= "Sensor Locations within Newcastle Upon-Tyne"
    )

    return fig

def plot_sensor_timseries(df: pd.DataFrame, variable: str) -> go.Figure:
    df = df.copy()

    df = df[df["Variable"] == variable]

    fig = px.line(
        df,
        x=df.index,
        y="Value",
        color="Sensor_Name",
        labels={
            "Value" : variable
        }
    )
    
    return fig

def create_air_polution_heatmap():
    pass

def create_decomposed_timeseries_plot():
    pass