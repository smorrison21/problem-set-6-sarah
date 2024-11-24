from shiny import App, render, ui, reactive
import pandas as pd
import anywidget
from shinywidgets import render_altair, output_widget 
import altair as alt
import json
import geopandas as gpd

app_ui = ui.page_fluid(
    ui.input_select(id = 'type_subtype', label = 'Select a Type-Subtype Combination:',
    choices = ["Accident - Major", "Accident - Minor", "Accident - Unclassified",
        "Jam - Heavy Traffic", "Jam - Light Traffic", "Jam - Moderate Traffic",
        "Jam - Stand-Still Traffic", "Jam - Unclassified", "Hazard - On Road",
        "Hazard - On Shoulder", "Hazard - Weather", "Hazard - Unclassified",
        "Road Closed - Construction", "Road Closed - Event", "Road Closed - Hazard",
        "Road Closed - Unclassified"]),
    ui.input_slider('hour', 'Hour of Day', 0, 23, 1),
    output_widget('scatter_plot'),
    ui.output_table("filtered_table"),
)


def server(input, output, session):
    @reactive.calc
    def full_data():
        return pd.read_csv("top_alerts_map_byhour/top_alerts_map_byhour.csv")


    @reactive.calc
    def filtered_data():
        # Filter data based on user input
        df = full_data()
        selected_combination = input.type_subtype()
        selected_hour = input.hour()

        # Apply filters for type_subtype and hour
        filtered_df = df[(df["type_subtype"] == selected_combination) & (df['hour'] == selected_hour)]
        return filtered_df

    @render.table()
    def filtered_table():
        return filtered_data()


    @render_altair
    def scatter_plot():
        # Read and convert GeoDataFrame to the appropriate format for Altair
        geo_data = gpd.read_file("./top_alerts_map/chicago-boundaries.geojson")
    
        # Confirm longitude and latitude are numeric
        filtered = filtered_data()
        filtered['longitude'] = pd.to_numeric(filtered['longitude'])
        filtered['latitude'] = pd.to_numeric(filtered['latitude'])

        # Create base map chart
        map_chart = alt.Chart(geo_data).mark_geoshape(
            fill=None,  # Transparent fill
            stroke="lightgray"
        ).properties(
            width=350,
            height=350
        ).project(
            type='identity',  # Assume coordinates are in WGS84
            reflectY=True 
        )

        scatter_chart = alt.Chart(filtered).mark_circle().encode(
            longitude='longitude:Q',
            latitude='latitude:Q', 
            size=alt.Size(
                'Count:Q', 
                title='Number of Observations', 
                scale=alt.Scale(type='pow', exponent=2, range=[1, 200]))
        )


        combined_chart = (map_chart + scatter_chart).configure_view(
            stroke=None  # Remove the border of the map chart
        ).properties(
            title=f"Chicago Neighborhood Map with {input.type_subtype()} Observations at {input.hour()} O'Clock"  
        ).configure_mark(
            opacity=0.7,
            color='darkblue'
        )

        return combined_chart
            
app = App(app_ui, server)

