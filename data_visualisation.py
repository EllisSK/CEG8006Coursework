import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

from shapely.geometry import Point

def create_all_sensors_within_boundary_plot(sensor_locations: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> go.Figure:
    sensor_locations["Broker_Name"].replace({
        "NE Travel Data API" : "Traffic Data",
        "aq_mesh_api" : "Air Quality Data"
    },
    inplace=True)
    
    sensor_locations["lat"] = sensor_locations.geometry.y
    sensor_locations["lon"] = sensor_locations.geometry.x

    mid_point = boundary.geometry.centroid.iloc[0]
    map_center = {"lat": mid_point.y, "lon": mid_point.x}
    
    fig = px.scatter_mapbox(
        sensor_locations, 
        lat="lat", 
        lon="lon", 
        mapbox_style="open-street-map",
        color="Broker_Name",
        zoom=11,
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

def create_simple_sensor_location_plot(sensor_locations: gpd.GeoDataFrame):
    fig = px.scatter_mapbox(
        sensor_locations, 
        lat="lat", 
        lon="lon", 
        mapbox_style="open-street-map",
        color="Broker_Name",
        zoom=11,
        labels={
            "Broker_Name" : "Type of Sensor",
        },
        title= "Map of Nearest Air Quality Sensors"
    )

def create_road_link_plot():
    pass

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