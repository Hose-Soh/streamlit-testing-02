import json
from datetime import datetime

from gwr import hydro_properties, met_properties, soil_properties, recharge_properties, ui_visuals
from gwr import soil_moisture
import ee
import geemap.foliumap as geemap
import streamlit as st
import base64
import logging
import ast
import branca.colormap as cm
import folium
from folium.plugins import MiniMap

logger = logging.getLogger(__name__)

# ______ GEE Authenthication ______
# Secrets
json_data = st.secrets["json_data"]
service_account = st.secrets["service_account"]

# Preparing values
json_object = json.loads(json_data, strict=False)
json_object = json.dumps(json_object)

# Authorising the app
credentials = ee.ServiceAccountCredentials(service_account, key_data=json_object)
ee.Initialize(credentials)



# _______________________ LAYOUT CONFIGURATION __________________________
# Add Omdena & Nitrolytics logo
logo_omdena = "./resources/omdena.png"
logo_nitrolytics = "./resources/nitrolytics.png"

st.set_page_config(page_title="Soil Data Exploration", page_icon=logo_omdena)

# Add title to page
st.title("Explore Soil Characteristics and Hydrological Properties of a Region")

# Add subtitle to page
st.write(
    "Discover Soil Content, Water Content, Potential Evapotranspiration, Water Recharge, Perched Water Level, Precipitation, and Soil Moisture! Enter longitude, latitude, initial date, and final date."
)

# shape the map
st.markdown(
    f"""
<style>
    .appview-container .main .block-container{{

        padding-top: {3}rem;
        padding-right: {2}rem;
        padding-left: {0}rem;
        padding-bottom: {0}rem;
    }}


</style>
""",
    unsafe_allow_html=True,
)

# __________________________Input Parameters________________________


# Show the code in the sidebar
with st.sidebar:
    # Create two columns
    col1, col2 = st.columns(2)

    # Display the first logo image in the first column with no margin
    col1.image(logo_omdena, width=100, use_column_width=False)

    # Display the second logo image in the second column with no margin
    col2.image(logo_nitrolytics, width=100, use_column_width=False)

st.sidebar.info("### ***Welcome***\n###### ***Soil Data*** ")

form = st.sidebar.form("Input Data")


def convert_to_point(coordinates):
    '''
    This function return a list as a ee.geometry.Point object
    '''
    return ee.Geometry.Point(coordinates)


def convert_to_polygon(coordinates):
    '''
    This function return a list of lists as a ee.geometry.Polygon object
    '''
    return ee.Geometry.Polygon(coordinates)


# Create a GEE map centered on the location of interest
my_map = geemap.Map(
    zoom=3,
    Draw_export=True,
)

with form:
    # Define the date range slider
    # Set default dates
    default_i_date = datetime(2015, 1, 1)
    default_f_date = datetime(2020, 1, 1)

    # Create date inputs with default values
    i_date = st.date_input(
        "Initial Date of Interest (Inclusive)",
        value=default_i_date,
        min_value=datetime(1992, 1, 1),
        max_value=datetime.now(),
    )
    f_date = st.date_input(
        "Final Date of Interest (Exclusive)",
        value=default_f_date,
        min_value=datetime(1992, 1, 1),
        max_value=datetime.now(),
    )

    # Taking geometry point input from user
    list_input = st.text_input("Enter the list:",
                               "[[-268.235321,22.435148],[-268.235321,22.480837],[-268.17627,22.480837],[-268.17627,22.435148],[-268.235321,22.435148]]")
    try:
        global parsed_list
        # default value for parsed_list
        parsed_list = [[-268.235321, 22.435148], [-268.235321, 22.480837], [-268.17627, 22.480837],
                       [-268.17627, 22.435148], [-268.235321, 22.435148]]
        parsed_list = ast.literal_eval(list_input)

        if isinstance(parsed_list, list):
            if len(parsed_list) == 1:
                coords_user = convert_to_point(parsed_list[0])
                global roi
                roi = coords_user
            elif len(parsed_list) > 1:

                coords_user = convert_to_polygon(parsed_list)
                roi = coords_user
            else:
                st.write("Invalid input. Please enter a non-empty list.")
        else:
            st.write("Invalid input. Please enter a valid list.")
    except Exception as e:
        st.write("Error:", e)

    # A nominal scale in meters of the projection to work in [in meters].
    scale = 1000

    # button to update visualization
    update_depth = st.form_submit_button("Show Result")

# __________________________Determination of Soil Texture and Properties____________________________________________


# Soil depths [in cm] where we have data.
olm_depths = [0, 10, 30, 60, 100, 200]

# Names of bands associated with reference depths.
olm_bands = ["b" + str(sd) for sd in olm_depths]

# ________________________________________Visualization for Soil Content___________________________________________


# Get soil property images
sand = soil_properties.get_soil_prop("sand")
clay = soil_properties.get_soil_prop("clay")
orgc = soil_properties.get_soil_prop("orgc")
# ph = dataset.select("PHIHOX").first()

# # Create the MiniMap
# mini_map = MiniMap(position='bottomright', width=150, height=150)
# my_map.add_child(mini_map)

# Set visualization parameter and addlayer on the map for sand content
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
sand_bands = sand.select(all_bands)
# Set visualization parameters.
sand_params = {
    "min": 0.1,
    "max": 1.0,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

# Define a sand colormap.
sand_colormap = cm.LinearColormap(
    colors=sand_params["palette"],
    vmin=sand_params["min"],
    vmax=sand_params["max"],
    
)

# Caption of the recharge colormap.
sand_colormap.caption = "Sand Content in % (kg / kg)"

# Add the first band as a base layer without time dimension
my_map.addLayer(sand.select(all_bands[0]), sand_params, 'Sand Band {}'.format(all_bands[0]))

# Add the remaining bands as separate layers with a time dimension
for band in all_bands[1:]:
    layer = geemap.ee_tile_layer(sand.select(band), sand_params, 'Sand Band {}'.format(band))
    my_map.add_child(layer)


# m.addLayer(sand_bands, vis_params, "Sand Content")
#my_map.add_time_slider(sand_bands, vis_params, labels=all_bands, time_interval=1)

# Add the colormaps to the map.
#my_map.add_child(sand_colormap)



my_map.add_colormap(width=3.6, height=0.05, vmin=sand_params["min"], vmax=sand_params["max"], palette=sand_params["palette"], 
                    vis_params=sand_params, label="Sand Content in % (kg / kg)", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 16))

##Set visualization parameter and addlayer on the map for clay content
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
clay_bands = clay.select(all_bands)

# Set visualization parameters.
clay_params = {
    "min": 0.01,
    "max": 0.4,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

# Define a sand colormap.
clay_colormap = cm.LinearColormap(
    colors=clay_params["palette"],
    vmin=clay_params["min"],
    vmax=clay_params["max"],
)

# Caption of the recharge colormap.
clay_colormap.caption = "Clay Content in % (kg / kg)"

# Add the first band as a base layer without time dimension
my_map.addLayer(clay.select(all_bands[0]), clay_params, 'Clay Band {}'.format(all_bands[0]))

# Add the remaining bands as separate layers with a time dimension
for band in all_bands[1:]:
    layer = geemap.ee_tile_layer(clay.select(band), clay_params, 'Clay Band {}'.format(band))
    my_map.add_child(layer)


# m.addLayer(sand_bands, vis_params, "Sand Content")
#my_map.add_time_slider(sand_bands, vis_params, labels=all_bands, time_interval=1)
# Add the colormaps to the map.
#my_map.add_child(clay_colormap)
my_map.add_colormap(width=3.55, height=0.05, vmin=clay_params["min"], vmax=clay_params["max"], palette=clay_params["palette"], 
                    vis_params=clay_params, label="Clay Content in % (kg / kg)", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 8))

#vis_clay = {'min': 0.01, 'max': 1, 'gamma': 2.0}

#my_map.addLayer(clay_bands, vis_clay, "Clay Content")
#my_map.add_time_slider(clay_bands, vis_clay, labels=all_bands, time_interval=1)

##Set visualization parameter and addlayer on the map for organic matter content
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
orgc_bands = orgc.select(all_bands)

# Set visualization parameters.
orgc_params = {
    "min": 0.001,
    "max": 0.01,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

# Define a sand colormap.
orgc_colormap = cm.LinearColormap(
    colors=orgc_params["palette"],
    vmin=orgc_params["min"],
    vmax=orgc_params["max"],
)

# Caption of the recharge colormap.
orgc_colormap.caption = "Organic Carbon Content in % (kg / kg)"

# Add the first band as a base layer without time dimension
my_map.addLayer(orgc.select(all_bands[0]), orgc_params, 'Organic Carbonic Band {}'.format(all_bands[0]))

# Add the remaining bands as separate layers with a time dimension
for band in all_bands[1:]:
    layer = geemap.ee_tile_layer(orgc.select(band), orgc_params, 'Organic Carbon Band {}'.format(band))
    my_map.add_child(layer)


# Add the colormaps to the map.
#my_map.add_child(orgc_colormap)
my_map.add_colormap(width=3.5, height=0.05, vmin=orgc_params["min"], vmax=orgc_params["max"], palette=orgc_params["palette"], 
                    vis_params=orgc_params, label="Organic Content in % (kg / kg)", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 0))

# Header for map
st.subheader("Google Earth Map")

# Display the map.
my_map.to_streamlit(height=600, responsive=True, scrolling=False)

# Add a layer control panel to the map.
my_map.addLayerControl()

# Obtain the Soil Profiles at the point
profile_sand = soil_properties.get_local_soil_profile_at_poi(
    sand, roi, scale, olm_bands
)
profile_clay = soil_properties.get_local_soil_profile_at_poi(
    clay, roi, scale, olm_bands
)
profile_orgc = soil_properties.get_local_soil_profile_at_poi(
    orgc, roi, scale, olm_bands
)

# ___________________________________________________Comparison of Soil Content Layers at Different Depths_____________________________________________________________
# Subheader and description for soil content visualization
st.subheader("Comparison of Soil Content Layers at Different Depths")

st.write(
    "This visualization presents a comparison of the soil content layers, including sand, clay, and organic carbon, at various depths from the surface to 200 cm. By comparing the soil content at different depths, we can gain a better understanding of the overall health and properties of the soil in the region. The depth of the soil is a critical factor in determining how well it retains moisture and nutrients, which is essential for plant growth and agriculture."
)

# Display the plot using Streamlit.
st.pyplot(
    ui_visuals.generate(profile_sand, profile_clay, profile_orgc, olm_bands, olm_depths)
)

# ___________________________________________________Hydraulic Properties of Soil at Different Depths_____________________________________________________________

# Conversion of organic carbon content into organic matter content.
orgm = soil_properties.convert_orgc_to_orgm(orgc)

# Organic matter content profile.
profile_orgm = soil_properties.get_local_soil_profile_at_poi(
    orgm, roi, scale, olm_bands
)

# Obtain Field Capacity and Wilting Points
field_capacity, wilting_point = hydro_properties.compute_hyrdo_properties(
    sand, clay, orgm, olm_bands
)

profile_wp = soil_properties.get_local_soil_profile_at_poi(
    wilting_point, roi, scale, olm_bands
)
profile_fc = soil_properties.get_local_soil_profile_at_poi(
    field_capacity, roi, scale, olm_bands
)

# Adding subheader and description for hydrolic properties
st.subheader("Hydraulic Properties of Soil at Different Depths")

# Second Map
my_map2 = geemap.Map(
    zoom=3,
    Draw_export=True,
)

# Adding Layers for Hydraulic Properties
##Set visualization parameter and addlayer on the map for organic matter content
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
orgm_bands = orgm.select(all_bands)

# Set visualization parameters.
orgm_params = {
    "min": 0.001,
    "max": 0.1,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

# Define a sand colormap.
orgm_colormap = cm.LinearColormap(
    colors=orgm_params["palette"],
    vmin=orgm_params["min"],
    vmax=orgm_params["max"],
)

# Caption of the recharge colormap.
orgm_colormap.caption = "Organic Matter in % (kg / kg)"

# Add the first band as a base layer without time dimension
my_map2.addLayer(orgm.select(all_bands[0]), orgm_params, 'Organic Matter Band {}'.format(all_bands[0]))

# Add the remaining bands as separate layers with a time dimension
for band in all_bands[1:]:
    layer = geemap.ee_tile_layer(orgm.select(band), orgm_params, 'Organic Matter Band {}'.format(band))
    my_map2.add_child(layer)


# Add the colormaps to the map.
#my_map.add_child(orgc_colormap)
my_map2.add_colormap(width=3.5, height=0.05, vmin=orgm_params["min"], vmax=orgm_params["max"], palette=orgm_params["palette"], 
                    vis_params=orgm_params, label="Organic Matter in % (kg / kg)", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 16))

##Set visualization parameter and addlayer on the map for field capacity
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
field_capacity_bands = field_capacity.select(all_bands)

# Set visualization parameters.
field_capacity_params = {
    "min": 0.08,
    "max": 0.5,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

# Define a sand colormap.
field_capacity_colormap = cm.LinearColormap(
    colors=field_capacity_params["palette"],
    vmin=field_capacity_params["min"],
    vmax=field_capacity_params["max"],
)

# Caption of the recharge colormap.
field_capacity_colormap.caption = "Organic Matter in % (kg / kg)"

# Add the first band as a base layer without time dimension
my_map2.addLayer(field_capacity.select(all_bands[0]), field_capacity_params, 'Field Capacity Band {}'.format(all_bands[0]))

# Add the remaining bands as separate layers with a time dimension
for band in all_bands[1:]:
    layer = geemap.ee_tile_layer(field_capacity.select(band), field_capacity_params, 'Field Capacity Band {}'.format(band))
    my_map2.add_child(layer)


# Add the colormaps to the map.
#my_map.add_child(orgc_colormap)
my_map2.add_colormap(width=3.55, height=0.05, vmin=field_capacity_params["min"], vmax=field_capacity_params["max"], palette=field_capacity_params["palette"], 
                    vis_params=field_capacity_params, label="Field Capacity in % (kg / kg)", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 8))


##Set visualization parameter and addlayer on the map for wilting point
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
wilting_point_bands = wilting_point.select(all_bands)

# Set visualization parameters.
wilting_point_params = {
    "min": 0.05,
    "max": 0.3,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

# Define a sand colormap.
wilting_point_colormap = cm.LinearColormap(
    colors=wilting_point_params["palette"],
    vmin=wilting_point_params["min"],
    vmax=wilting_point_params["max"],
)

# Caption of the recharge colormap.
wilting_point_colormap.caption = "Wilting Point in % (kg / kg)"

# Add the first band as a base layer without time dimension
my_map2.addLayer(wilting_point.select(all_bands[0]), wilting_point_params, 'Wilting Point Band {}'.format(all_bands[0]))

# Add the remaining bands as separate layers with a time dimension
for band in all_bands[1:]:
    layer = geemap.ee_tile_layer(wilting_point.select(band), wilting_point_params, 'Wilting Point Band {}'.format(band))
    my_map2.add_child(layer)


# Add the colormaps to the map.
#my_map.add_child(orgc_colormap)
my_map2.add_colormap(width=3.34, height=0.05, vmin=wilting_point_params["min"], vmax=wilting_point_params["max"], palette=wilting_point_params["palette"], 
                    vis_params=wilting_point_params, label="Wilting Point in % (kg / kg)", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 0))


# Display the my_map2.
my_map2.to_streamlit(height=600, responsive=True, scrolling=False)
# Add a layer control panel to the map.
my_map2.addLayerControl()

st.write(
    "This visualization displays the water content of soil at the wilting point and field capacity at different depths (0, 10, 30, 60, 100, and 200 cm). Water content at the wilting point represents the minimum amount of soil water that a plant requires to avoid wilting, while water content at field capacity indicates the maximum amount of water that the soil can hold against the force of gravity. By examining these properties at different depths, we can gain insight into the water retention capacity of the soil and understand how it affects plant growth and water availability."
)

st.pyplot(
    ui_visuals.generate_hydraulic_props_chart(
        profile_wp, profile_fc, olm_bands, olm_depths
    )
)

# _____________________________________________Getting Meteorological Datasets__________________________________________
meteo = met_properties.get_mean_monthly_meteorological_data(i_date, f_date)
meteo_df = met_properties.get_mean_monthly_meteorological_data_for_roi_df(roi, scale, meteo)

pr = met_properties.get_precipitation_data_for_dates(i_date, f_date)
pet = met_properties.get_potential_evaporation_for_dates(i_date, f_date)

# Third Map
my_map3 = geemap.Map(
    zoom=3,
    Draw_export=True,
)

##Set visualization parameter and addlayer on the map for Precipitation

# Set visualization parameters.
pr_params = {
    "bands": ["precipitation"],
    "min": 0,
    "max": 17,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

# # Define a sand colormap.
# pr_colormap = cm.LinearColormap(
#     colors=pr_params["palette"],
#     vmin=pr_params["min"],
#     vmax=pr_params["max"],
# )

# # Caption of the recharge colormap.
# pr_colormap.caption = "Precipitation in mm/d"

my_map3.addLayer(pr, pr_params, "Precipitation")


# Add the colormaps to the map.
#my_map.add_child(orgc_colormap)
my_map3.add_colormap(width=3.46, height=0.05, vmin=pr_params["min"], vmax=pr_params["max"], palette=pr_params["palette"], 
                    vis_params=pr_params, label="Precipitation in mm", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 16))


##Set visualization parameter and addlayer on the map for Potential Evapotranspiration

# Set visualization parameters.
pet_params = {
    "bands": ["PET"],
    "min": 25,
    "max": 600,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

# # Define a sand colormap.
# pr_colormap = cm.LinearColormap(
#     colors=pr_params["palette"],
#     vmin=pr_params["min"],
#     vmax=pr_params["max"],
# )

# # Caption of the recharge colormap.
# pr_colormap.caption = "Precipitation in mm/d"

my_map3.addLayer(pet, pet_params, "Potential Evapotranspiration")


# Add the colormaps to the map.
#my_map.add_child(orgc_colormap)
my_map3.add_colormap(width=3.45, height=0.05, vmin=pet_params["min"], vmax=pet_params["max"], palette=pet_params["palette"], 
                    vis_params=pet_params, label="Potential Evapotranspiration in kg/m^2", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 8))

# _____________________________________________Display Meteorological Dataset_____________________________________________
# Adding subheader and description for mateorological data
st.subheader(
    "Precipitation and Potential Evapotranspiration Data for Region of Interest"
)

st.write(
    "This section displays a dataframe of precipitation and potential evapotranspiration data for a selected region of interest within a given time frame. The data is presented in columns, with each column representing a specific variable related to the water cycle."
)
# Add a description of the columns
st.write(
    "-PR represents Precipitation, which refers to the amount of water that falls to the ground in the form of rain, snow, sleet, or hail."
)
st.write(
    "-PET represents Potential Evapotranspiration, which is the amount of water that would evaporate and transpire from an area if it had an unlimited supply of water. It is a measure of the atmospheric demand for water."
)
# Display the DataFrame
st.write(meteo_df)

# Add a download button to download the CSV file
csv = meteo_df.to_csv(index=True)
b64 = base64.b64encode(csv.encode()).decode()  # encode as CSV string
href = f'<a href="data:file/csv;base64,{b64}" download="meteo_data.csv">Download Meteorological Data</a>'
st.markdown(href, unsafe_allow_html=True)

st.write(
    "The visualization displays the trends of both the mean precipitation and mean potential evapotranspiration over time for the region of interest, allowing users to analyze how these variables have changed in the selected region."
)

st.pyplot(ui_visuals.generate_pr_pet_graph(meteo_df))

# ____________________Comparison of Precipitation, Potential Evapotranspiration, and Recharge__________________________

zr = ee.Image(0.5)
p = ee.Image(0.5)

# Apply the function to field capacity and wilting point.
fcm = recharge_properties.olm_prop_mean(field_capacity, "fc_mean")
wpm = recharge_properties.olm_prop_mean(wilting_point, "wp_mean")

# Calculate the theoretical available water.
taw = recharge_properties.calculate_available_water(fcm, wpm, zr)

# Calculate the stored water at the field capacity.
stfc = recharge_properties.calculate_stored_water_at_fc(taw, p)

# Define the initial time (time0) according to the start of the collection.
time0 = meteo.first().get("system:time_start")

recharge_df, recharge_collection = recharge_properties.get_monthly_mean_recharge_at_roi_df(meteo, roi, scale, stfc, fcm,
                                                                                           wpm, time0)

# subheader
st.subheader("Comparison of Precipitation, Potential Evapotranspiration, and Recharge")

# Display the DataFrame
st.write(recharge_df)

# Add a download button to download the CSV file
csv = recharge_df.to_csv(index=True)
b64 = base64.b64encode(csv.encode()).decode()  # encode as CSV string
href = f'<a href="data:file/csv;base64,{b64}" download="water_recharge_data.csv">Download Water Recharge Data</a>'
st.markdown(href, unsafe_allow_html=True)

st.write(
    "The visualization shows a comparison of precipitation, potential evapotranspiration, and recharge over time.This visualization allows you to easily compare the trends of each variable and identify any patterns or anomalies that may be present. By understanding the relationships between precipitation, potential evapotranspiration, and recharge, it's easier to gain insight into the water balance of the region and its overall water availability."
)

st.pyplot(ui_visuals.generate_pr_pet_rech_graph(recharge_df))

# Resample the pandas dataframe on a yearly basis making the sum by year.
rdfy = recharge_df.resample("Y").sum()

# Calculate the mean value.
annual_mean_recharge_df = recharge_properties.get_mean_annual_recharge_at_roi_df(meteo, roi, scale, stfc, fcm, wpm,
                                                                                 time0)


##Set visualization parameter and addlayer on the map for Potential Evapotranspiration

# # Set visualization parameters.
# rech_params = {
#     "bands": "rech",
#     "min": 0,
#     "max": 2,
#     "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
# }

# my_map3.addLayer(recharge_collection, rech_params, "Recharge Water")


# # Add the colormaps to the map.
# #my_map.add_child(orgc_colormap)
# my_map3.add_colormap(width=3.4, height=0.05, vmin=rech_params["min"], vmax=rech_params["max"], palette=rech_params["palette"], 
#                     vis_params=rech_params, label="Water Recharge", label_size=6, label_weight='normal', tick_size=8,
#                     bg_color='white', position=(0, 0))

# Display the map.
my_map3.to_streamlit(height=600, responsive=True, scrolling=False)
# Add a layer control panel to the map.
my_map3.addLayerControl()

st.write(
    "The mean annual recharge at across region of interest"
)
st.write(
    annual_mean_recharge_df[['mean-annual-rech']].round(2).rename(columns={'mean-annual-rech': 'Mean Annual Recharge'}))

# ____________________ Soil Moisture __________________________
# Getting Soil Moisture Datasets
soilmois1 = soil_moisture.get_mean_monthly_smap_data(i_date, f_date)
soilmois_df = soil_moisture.get_mean_monthly_smap_data_for_roi_df(roi, scale, soilmois1)

# Soil Moisture Map
my_map4 = geemap.Map(
    zoom=3,
    Draw_export=True,
)

# # Adding Layers for Soil Moisture data
# soilMoistureVis = {
#     'min': 0.0,
#     'max': 280.0,
#     'palette': ['00FFFF', '0000FF'],
# }


# soil_moisture_map.addLayer(soilmois1.select(['ssm']), soilMoistureVis, "Surface Soil Moisture")
# soil_moisture_map.addLayer(soilmois1.select(['susm']), soilMoistureVis, "Subsurface Soil Moisture")


##Set visualization parameter and addlayer on the map for soil moisture
# Set visualization parameters.
ssm_params = {
    "bands": 'ssm',
    "min": 0,
    "max": 1000,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

my_map4.addLayer(soilmois1, ssm_params, "Surface soil moisture")


# Add the colormaps to the map.
#my_map.add_child(orgc_colormap)
my_map4.add_colormap(width=3.45, height=0.05, vmin=ssm_params["min"], vmax=ssm_params["max"], palette=ssm_params["palette"], 
                    vis_params=ssm_params, label="Surface soil moisture in mm", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 18))

susm_params = {
    "bands": 'susm',
    "min": 0,
    "max": 3000,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
    
}

my_map4.addLayer(soilmois1, susm_params, "Subsurface soil moisture")


# Add the colormaps to the map.
#my_map.add_child(orgc_colormap)
my_map4.add_colormap(width=3.45, height=0.05, vmin=susm_params["min"], vmax=susm_params["max"], palette=susm_params["palette"], 
                    vis_params=susm_params, label="Subsurface soil moisture in mm", label_size=6, label_weight='normal', tick_size=8,
                    bg_color='white', position=(0, 0))

# Display Meteorological Dataset
st.subheader(
    "Soil Moisture Data for Region of Interest"
)
my_map4.to_streamlit(height=300, responsive=True, scrolling=False)

# Add a layer control panel to the map.
my_map4.addLayerControl()

# Display the DataFrame
st.write(soilmois_df)

# Add a download button to download the CSV file
csv = soilmois_df.to_csv(index=True)
b64 = base64.b64encode(csv.encode()).decode()  # encode as CSV string
href = f'<a href="data:file/csv;base64,{b64}" download="soilmoisture_data.csv">Download Soil Moisture Data</a>'
st.markdown(href, unsafe_allow_html=True)

st.pyplot(ui_visuals.generate_soil_moisture_graph(soilmois_df))
