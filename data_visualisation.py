import datetime

import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import griddata

from shapely.geometry import Point
from plotly.subplots import make_subplots
from pathlib import Path

def save_figure(fig: go.Figure, name: str):
    """
    Function that saves a figure as a vector image, scaling any raster components.
    """
    
    figure_directory = Path(f"outputs/figures/{name}.svg")
    fig.write_image(figure_directory, format="svg", scale=3)

def create_all_sensors_within_boundary_plot(sensor_locations: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> go.Figure:
    """
    Function that creates a plot of sensors within the boundary polygon.

    Returns a Plotly Graph Objects Figure.
    """
    
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

    #Calculates a mid point to focus the view on from the centre of sensor locations.
    mid_point = proj_boundary.geometry.centroid.iloc[0]
    mid_point = gpd.GeoSeries([mid_point], crs=27700).to_crs(epsg=4326).iloc[0]
    map_center = {"lat": mid_point.y, "lon": mid_point.x}
    
    #Add the sensors as points
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
            
    #Add the boundary as lines        
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
    """
    Function that creates a plot of road links between traffic sensors.

    Returns a Plotly Graph Objects Figure.
    """ 
    
    
    fig = go.Figure()

    lats = []
    lons = []

    n = len(road_geom)

    #For each geometry, create a list of points to draw lines through 
    for multi_line in road_geom.geometry:
        for line in multi_line.geoms:
            x, y = line.xy
            lats.extend(y)
            lons.extend(x)
            lats.append(None)
            lons.append(None)

    #Add the points as lines
    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode="lines",
        line=dict(width=3, color="red"),
        name="Traffic Flow Routes",
        showlegend=True,
    ))

    #Update centre of map and zoom
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
    """
    Function that creates a plot of sensors.

    Returns a Plotly Graph Objects Figure.
    """
    
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
    """
    Function that creates a plot of sensors, road links and a building location.

    Returns a Plotly Graph Objects Figure.
    """
    
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
        name="Proposed Building",
        text=["Proposed Site Location"],
        showlegend=True
    ))
    
    return fig

def create_correlation_heatmap(corr_df: pd.DataFrame) -> go.Figure:
    """
    Function that creates a heatmap showing how correlated sensors and their variables are with each other.

    Returns a Plotly Graph Objects Figure.
    """
    
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

def create_decomposed_timeseries_plot(decomp_df: pd.DataFrame) -> go.Figure:
    """
    Function that creates multiple plots of a timeseries decomposition, showing average values for defined periods.

    Returns a Plotly Graph Objects Figure.
    """
    
    #Convert columns in data into axis titles
    known_periods = {
        "Daily": ("hour", "Average Daily Pattern"),
        "Weekly": ("dayofweek", "Average Weekly Pattern"),
        "Monthly": ("month", "Average Monthly Pattern")
    }

    #Ensure period columns are picked up properly.
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
    """
    Function that creates multiple plots of a timeseries decomposition, showing full decomposition and trend over the data time period.

    Returns a Plotly Graph Objects Figure.
    """
    
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

def create_air_polution_heatmap(air_quality_timseries: pd.DataFrame, air_quality_sensors: gpd.GeoDataFrame, target_datetime: datetime.datetime, variable: str) -> go.Figure:
    """
    Function that creates a density heatmap of air polution from multiple sensors at a given datetime in the timeseries.

    Returns a Plotly Graph Objects Figure.
    """
    
    #Check required datetime has data
    if target_datetime not in air_quality_timseries.index:
        raise ValueError(f"Timestamp {target_datetime} not found in timeseries index.")

    #Get requested data
    data_row = air_quality_timseries.loc[target_datetime]
    suffix = f"_{variable}"
    relevant_cols = [col for col in data_row.index if col.endswith(suffix)]

    if not relevant_cols:
        raise ValueError(f"No columns found ending with \"{suffix}\"")

    parsed_data = []
    for col in relevant_cols:
        sensor_name = col.rsplit("_", 1)[0]
        value = data_row[col]
        parsed_data.append({"Sensor_Name": sensor_name, "Value": value})

    df_values = pd.DataFrame(parsed_data)

    merged_df = df_values.merge(air_quality_sensors, on="Sensor_Name", how="inner")
    merged_df = gpd.GeoDataFrame(merged_df, geometry="geometry")
    merged_df = merged_df.dropna(subset=["Value"])

    if merged_df.empty:
        raise ValueError("No matching sensor data found after merging and cleaning.")

    merged_df["lat"] = merged_df.geometry.y
    merged_df["lon"] = merged_df.geometry.x

    #Create a grid to place interpolated values onto to avoid no data gaps between sensors
    grid_x, grid_y = np.mgrid[
        merged_df["lon"].min()-0.01 : merged_df["lon"].max()+0.01 : 100j,
        merged_df["lat"].min()-0.01 : merged_df["lat"].max()+0.01 : 100j
    ]

    #Set the values on the grid as linear interpolation from values at sensor points
    grid_z = griddata(
        points=(merged_df["lon"], merged_df["lat"]),
        values=merged_df["Value"],
        xi=(grid_x, grid_y),
        method="linear"
    )

    flat_lon = grid_x.flatten()
    flat_lat = grid_y.flatten()
    flat_val = grid_z.flatten()

    mask = ~np.isnan(flat_val)
    flat_lon = flat_lon[mask]
    flat_lat = flat_lat[mask]
    flat_val = flat_val[mask]

    fig = go.Figure()

    fig.add_trace(go.Densitymapbox(
        lat=flat_lat,
        lon=flat_lon,
        z=flat_val,
        radius=15,
        colorscale="RdYlGn_r",
        opacity=0.7,
        zmin=0,
        zmax=80,
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scattermapbox(
        lat=merged_df["lat"],
        lon=merged_df["lon"],
        mode="markers",
        marker=dict(size=10, color="black", symbol="circle"),
        text=merged_df["Sensor_Name"],
        hovertext=merged_df["Value"].apply(lambda x: f"{x:.2f}"),
        hovertemplate="<b>%{text}</b><br>Value: %{hovertext}<extra></extra>"
    ))

    fig.update_layout(
        title=f"Interpolated {variable} - {target_datetime}",
        mapbox_style="open-street-map",
        mapbox=dict(
            center=dict(lat=merged_df["lat"].mean(), lon=merged_df["lon"].mean()),
            zoom=12
        ),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        showlegend=False
    )

    return fig

def create_sensor_boxplots(air_quality_timeseries: pd.DataFrame, sensor_name: str) -> go.Figure:
    """
    Function that creates multiple box plots of air quality data from a sensor.

    Returns a Plotly Graph Objects Figure.
    """
    
    fig = go.Figure()
    
    prefix = f"{sensor_name}_"
    relevant_cols = [col for col in air_quality_timeseries.columns if col.startswith(prefix)]
    
    #Dont show wind data
    excluded_vars = ["Wind Speed", "Wind Direction"]

    for col in relevant_cols:
        variable_label = col[len(prefix):]
        
        if variable_label in excluded_vars:
            continue
        
        fig.add_trace(go.Box(
            y=air_quality_timeseries[col],
            name=variable_label,
            boxpoints=False
        ))

    fig.update_layout(
        title=f"Pollution Statistics for sensor {sensor_name}",
        yaxis_title="Concentration (µg/m³)",
        xaxis_title="Pollutant Variable",
        template="plotly_white",
        showlegend=False,
        font=dict(family="Arial", size=12)
    )

    return fig