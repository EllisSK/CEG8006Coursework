import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

from shapely.geometry import Point
from plotly.subplots import make_subplots
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

    n = len(road_geom)

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
        title=f"Closest {n} Traffic Sensor Routes"
    )

    return fig

def create_air_quality_sensor_location_plot(sensor_locations: gpd.GeoDataFrame) -> go.Figure:
    sensor_locations = sensor_locations.copy()
    
    n = len(sensor_locations)

    sensor_locations["lat"] = sensor_locations.geometry.y
    sensor_locations["lon"] = sensor_locations.geometry.x

    fig = px.scatter_mapbox(
        sensor_locations,
        lat="lat",
        lon="lon", 
        mapbox_style="open-street-map",
        color="Broker_Name",
        zoom=10,
        center=dict(lat=54.983, lon=-1.6178),
        title= f"Map of {n} Closest Air Quality Sensors"
    )

    return fig

def create_air_quality_road_links_site_location_plot(sensor_locations: gpd.GeoDataFrame, road_geom: gpd.GeoDataFrame, building_location: Point):
    sensor_locations = sensor_locations.copy()
    road_geom = road_geom.copy()

    sensor_locations["lat"] = sensor_locations.geometry.y
    sensor_locations["lon"] = sensor_locations.geometry.x

    names_dict = {
        "aq_mesh_api" : "Air Quality Data"
    }

    sensor_locations["Broker_Name"] = sensor_locations["Broker_Name"].replace(names_dict)
    
    fig = px.scatter_mapbox(
        sensor_locations, 
        lat="lat", 
        lon="lon", 
        mapbox_style="open-street-map",
        color="Broker_Name",
        zoom=11.5,
        center=dict(lat=54.983, lon=-1.6178),
        title= "Map of Air Quality and Traffic Sensors Around the Proposed Site",
        labels= {"Broker_Name" : "Type of Sensor"}
    )

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

    fig.add_trace(go.Scattermapbox(
        lat=[building_location.y],
        lon=[building_location.x],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=15,
        ),
        name='Proposed Building',
        text=["Proposed Site Location"],
        showlegend=True
    ))
    
    return fig

def create_correlation_heatmap(corr_df: pd.DataFrame) -> go.Figure:
    clean_df = corr_df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    
    fig = px.imshow(
        clean_df,
        labels={
            "x": "Features",
            "y": "Features",
            "color": "Correlation"
        },
        template="presentation",
        color_continuous_scale=["red", "yellow", "green"],
        range_color=[-1, 1]
    )
    
    fig.update_layout(
        width=1000,
        height=1000,
        xaxis_title="Features",
        yaxis_title="Features",
        title="Correlation Heatmap",
        xaxis={
            "automargin": True,
            "tickmode": "linear",
            "dtick": 1,
            "tickangle": -90,
            "tickfont": {"size": 10}
        },
        yaxis={
            "automargin": True,
            "tickmode": "linear",
            "dtick": 1,
            "tickfont": {"size": 10}
        },
        coloraxis_colorbar={
            "thickness": 30,
            "len": 1
        }
    )
    
    return fig

def create_air_quality_line_plot():
    pass

def create_journey_time_line_plot():
    pass

def create_decomposed_timeseries_plot(decomp_df: pd.DataFrame) -> go.Figure:
    known_periods = {
        "Daily": ("hour", "Average Daily Pattern"),
        "Weekly": ("dayofweek", "Average Weekly Pattern"),
        "Monthly": ("month", "Average Monthly Pattern")
    }

    found_periods = [col for col in decomp_df.columns if col in known_periods]

    fig = make_subplots(
        rows=len(found_periods), 
        cols=1, 
        subplot_titles=[known_periods[col][1] for col in found_periods],
        vertical_spacing=0.1
    )

    for i, col in enumerate(found_periods):
        time_attr = known_periods[col][0]
        
        avg_profile = decomp_df[col].groupby(getattr(decomp_df.index, time_attr)).mean()
        
        fig.add_trace(
            go.Scatter(
                x=avg_profile.index,
                y=avg_profile.values,
                name=col + " Average",
                mode="lines+markers",
                line=dict(color="firebrick", width=2)
            ),
            row=i+1, 
            col=1
        )
        
        fig.add_hline(y=0, line_dash="dot", row=i+1, col=1, line_color="gray")

    fig.update_layout(
        height=300 * len(found_periods),
        title_text="Representative Seasonal Profiles (Averages)",
        showlegend=False
    )
    
    if "Weekly" in found_periods:
        row_idx = found_periods.index("Weekly") + 1
        fig.update_xaxes(
            tickmode="array",
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            row=row_idx, col=1
        )

    return fig

def create_decomposed_trend_plot(decomp_df: pd.DataFrame) -> go.Figure:
    n_components = decomp_df.shape[1]
    cols = decomp_df.columns

    fig = make_subplots(
        rows=n_components, 
        cols=1, 
        shared_xaxes=True,
        subplot_titles=cols,
        vertical_spacing=0.05
    )

    for i, col in enumerate(cols):
        fig.add_trace(
            go.Scatter(
                x=decomp_df.index, 
                y=decomp_df[col], 
                name=col,
                mode="lines",
                line=dict(width=1.5, color="navy" if col == "Original" else "teal")
            ),
            row=i+1, 
            col=1
        )

    fig.update_layout(
        height=300 * n_components,
        title_text="Timeseries Decomposition Trends",
        showlegend=False
    )

    return fig

def create_air_polution_heatmap():
    pass