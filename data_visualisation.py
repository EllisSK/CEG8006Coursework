import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

from shapely.geometry import Point
from pathlib import Path

def save_figure(fig: go.Figure, name: str):
    figure_directory = Path(f"outputs/figures/{name}.svg")
    fig.write_image(figure_directory, format="svg", scale=3)

def create_all_sensors_within_boundary_plot(sensor_locations: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> go.Figure:
    sensor_locations = sensor_locations.copy()
    boundary = boundary.copy()

    names_dict = {
        "NE Travel Data API" : "Traffic Data",
        "aq_mesh_api" : "Air Quality Data"
    }
    
    sensor_locations["Broker_Name"] = sensor_locations["Broker_Name"].replace(names_dict)
    
    sensor_locations["lat"] = sensor_locations.geometry.y
    sensor_locations["lon"] = sensor_locations.geometry.x

    proj_boundary = boundary.to_crs(epsg=27700)

    mid_point = proj_boundary.geometry.centroid.iloc[0]
    mid_point = gpd.GeoSeries([mid_point], crs=27700).to_crs(epsg=4326).iloc[0]
    map_center = {"lat": mid_point.y, "lon": mid_point.x}
    
    fig = px.scatter_mapbox(
        sensor_locations, 
        lat="lat", 
        lon="lon", 
        mapbox_style="open-street-map",
        color="Broker_Name",
        zoom=9.7,
        center=map_center,
        labels={
            "Broker_Name" : "Type of Sensor",
        },
        title= "Map of Air Quality and Traffic Sensors within Newcastle Upon-Tyne"
    )

    fig.update_traces(marker={'size': 15})

    boundary_lons = []
    boundary_lats = []

    parts = boundary.geometry.exterior

    for part in parts:
        x, y = part.xy
        boundary_lons.extend(list(x) + [None])
        boundary_lats.extend(list(y) + [None])
            
    fig.add_trace(go.Scattermapbox(
        mode="lines",
        lon=boundary_lons,
        lat=boundary_lats,
        marker={"size": 0},
        line={"width": 5, "color": "black"},
        name="Newcastle Boundary",
        showlegend=True,
        hoverinfo="skip"
    ))

    return fig

def create_road_link_plot(road_geom: gpd.GeoDataFrame) -> go.Figure:
    fig = go.Figure()

    lats = []
    lons = []

    for multi_line in road_geom.geometry:
        for line in multi_line.geoms:
            x, y = line.xy
            lats.extend(y)
            lons.extend(x)
            lats.append(None)
            lons.append(None)

    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode="lines",
        line=dict(width=3, color="red"),
        name="Traffic Flow Routes",
        showlegend=True,
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=54.983, lon=-1.6178),
            zoom=11
        ),
        title="Traffic Sensor Routes"
    )

    return fig

def create_air_quality_sensor_location_plot():
    pass

def create_air_quality_road_links_site_location_plot():
    pass

def create_air_quality_line_plot():
    pass

def create_journey_time_line_plot():
    pass

def create_decomposed_timeseries_plot():
    pass

def create_air_polution_heatmap():
    pass