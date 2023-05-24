import json
from datetime import datetime

from gwr import hydro_properties, met_properties, soil_properties, recharge_properties, ui_visuals
import ee
import geemap.foliumap as geemap
import streamlit as st
import base64
import logging
import ast
import folium

logger = logging.getLogger(__name__)


# ______ GEE Authenthication ______

# _____ STREAMLIT _______

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
    
    #Taking geometry point input from user
    list_input = st.text_input("Enter the list:", "[[-268.235321,22.435148],[-268.235321,22.480837],[-268.17627,22.480837],[-268.17627,22.435148],[-268.235321,22.435148]]")
    try:
        global parsed_list
        #default value for parsed_list
        parsed_list = [[-268.235321,22.435148],[-268.235321,22.480837],[-268.17627,22.480837],[-268.17627,22.435148],[-268.235321,22.435148]]
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

# _______________________________________________________Determination of Soil Texture and Properties____________________________________________


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

#$Set visualization parameter and addlayer on the map for sand content
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
sand_bands = sand.select(all_bands)
# Set visualization parameters.
vis_sand = {'min': 0.01, 'max': 1}

my_map.addLayer(sand_bands, vis_sand, "Sand Content")
my_map.add_time_slider(sand_bands, vis_sand, labels=all_bands, time_interval=1)

##Set visualization parameter and addlayer on the map for clay content
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
clay_bands = clay.select(all_bands)
vis_clay = {'min': 0.01, 'max': 1, 'gamma': 2.0}

my_map.addLayer(clay_bands, vis_clay, "Clay Content")
my_map.add_time_slider(clay_bands, vis_clay, labels=all_bands, time_interval=1)

##Set visualization parameter and addlayer on the map for organic matter content
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
orgc_bands = orgc.select(all_bands)
vis_orgc = {'min': 0.01, 'max': 1, 'gamma': 2.0}

my_map.addLayer(orgc_bands, vis_orgc, "Organic Carbon Content")
my_map.add_time_slider(orgc_bands, vis_orgc, labels=all_bands, time_interval=1)
# # Set visualization parameters.
# vis_params = {
#     "min": 0.01,
#     "max": 1,
#     "opacity": 1,
# }

# # Add the sand content data to the map object.
# my_map.addLayer(sand, vis_params, "Sand Content")

# Add a marker at the location of interest.
# Add a marker at the location of interest.
#folium.Marker(parsed_list, popup="point of interest").add_to(my_map)
# Create a polygon and add it to the map

# Create a polygon and add it to the map
# polygon = folium.Polygon(locations=parsed_list, popup="Area of interest")
# polygon.add_to(my_map)

# # Create a feature group and add the polygon to it
# feature_group = folium.FeatureGroup(name='My Layer')
# feature_group.add_child(polygon)

# Add the feature group to the map
# my_map.add_child(polygon)

# Add layer control to the map
#folium.LayerControl().add_to(my_map)

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

#Second Map
my_map2 = geemap.Map(
    zoom=3,
    Draw_export=True,
)


#Adding Layers for Hydraulic Properties
##Set visualization parameter and addlayer on the map for organic matter content
all_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
orgm_bands = orgm.select(all_bands)
vis_orgm = {'min': 0.01, 'max': 1, 'gamma': 2.0, "opacity": 1}

my_map2.addLayer(orgm_bands, vis_orgm, "Organic Matter Content")
my_map2.add_time_slider(orgc_bands, vis_orgm, labels=all_bands, time_interval=1)

#Adding layer for Field capacity 
vis_fieldcapacity = {
    "min": 0.01,
    "max": 1,
    "opacity": 1,
    "color": {
        "gradient": "linear",
        "stops": [
            [0, "lightblue"],
            [0.25, "skyblue"],
            [0.5, "royalblue"],
            [0.75, "navy"],
            [1, "darkblue"]
        ]
    }
}

my_map2.addLayer(field_capacity, vis_fieldcapacity, "Field Capacity")

#Adding layer for wilting point 
vis_wilting = {
    "min": 0.01,
    "max": 1,
    "opacity": 1,
    "color": {
        "gradient": "linear",
        "stops": [
            [0, "lightblue"],
            [0.25, "skyblue"],
            [0.5, "royalblue"],
            [0.75, "navy"],
            [1, "darkblue"]
        ]
    }
}

my_map2.addLayer(wilting_point, vis_wilting, "Wilting Point")

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


# _____________________________________________Getting Meteorological Datasets_____________________________________________
meteo = met_properties.get_mean_monthly_meteorological_data(i_date, f_date)
meteo_df = met_properties.get_mean_monthly_meteorological_data_for_roi_df(roi, scale, meteo)

pr = met_properties.get_precipitation_data_for_dates(i_date, f_date)
pet = met_properties.get_potential_evaporation_for_dates(i_date, f_date)

#ThirdMap
my_map3 = geemap.Map(
    zoom=3,
    Draw_export=True,
)

#Adding Layers for Pricipitation data
vis_pr = {
    'min': 1.0,
    'max': 17.0,
    'palette': ['001137', '0aab1e', 'e7eb05', 'ff4a2d', 'e90000'],

}

my_map3.addLayer(pr, vis_pr, "Precipitation")

#Adding Layers for Potential Evaporation data
vis_pet = {
    'bands': ["PET"],
    'min': 0.0,
    'max': 300.0,
    'palette':  ['001137', '0aab1e', 'e7eb05', 'ff4a2d', 'e90000']}


my_map3.addLayer(pet, vis_pet, "Potential Evaporation")

# _____________________________________________Display Meteorological Dataset_____________________________________________
# Adding subheader and description for mateorological data
st.subheader(
    "Precipitation and Potential Evapotranspiration Data for Region of Interest"
)

# Display the my_map3.
my_map3.to_streamlit(height=600, responsive=True, scrolling=False)
# Add a layer control panel to the map.
my_map3.addLayerControl()

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

# ________________________________________________Comparison of Precipitation, Potential Evapotranspiration, and Recharge_________________________________________________

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

recharge_df, recharge_collection, _ = recharge_properties.get_monthly_mean_recharge_at_roi_df(meteo, roi, scale, stfc, fcm, wpm, time0)

# subheader
st.subheader("Comparison of Precipitation, Potential Evapotranspiration, and Recharge")

# # description
# st.write("This section provides a comparison of precipitation, potential evapotranspiration, and recharge for the selected region of interest. The data is presented in a dataframe.")
# st.write("- PR: Precipitation is the amount of water that falls to the ground in the form of rain, snow, sleet, or hail.")
# st.write("- PET: Potential Evapotranspiration is the amount of water that would evaporate and transpire from an area if it had an unlimited supply of water. It is a measure of the atmospheric demand for water.")
# st.write("- Rech: Recharge is the process by which water enters an aquifer, typically through infiltration of precipitation or other surface water sources.")
# st.write("- ST: Soil moisture is the amount of water held in the soil that is available for plant uptake and other uses. It can be an important factor in recharge, as it affects the amount of water that can infiltrate into the groundwater system.")
# st.write("- APWL: Average Perched Water Level is the average height of the water table or perched water body in an aquifer.")


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
annual_mean_recharge_df = recharge_properties.get_mean_annual_recharge_at_roi_df(meteo, roi, scale, stfc, fcm, wpm, time0)

my_map4 = geemap.Map(
    zoom=3,
    Draw_export=True,
)

# Set visualization parameters for recharge.
rech_vis_params = {
    "bands": "rech",
    "min": 0,
    "max": 500,
    "opacity": 1,
    "palette": ["red", "orange", "yellow", "green", "blue", "purple"],
}


my_map4.addLayer(recharge_collection, rech_vis_params, "Recharge Water")

# Display the map.
my_map4.to_streamlit(height=600, responsive=True, scrolling=False)
# Add a layer control panel to the map.
my_map4.addLayerControl()

st.write(
    "The mean annual recharge at across region of interest"
)
st.write(annual_mean_recharge_df[['mean-annual-rech']].round(2).rename(columns={'mean-annual-rech': 'Mean Annual Recharge'}))


# #___________________________________Groundwater recharge comparison between multiple places_________________________________________

# def get_local_recharge(i_date, f_date, lon, lat, scale):
#     """
#     Returns a pandas df describing the cumulative groundwater
#     recharge by month
#     """
#     # Define the location of interest with a point.
#     poi = ee.Geometry.Point(lon, lat)

#     # Evaluate the recharge around the location of interest.
#     rarr = rech_coll.filterDate(i_date, f_date).getRegion(poi, scale).getInfo()

#     # Transform the result into a pandas dataframe.
#     rdf =ee_utils.ee_array_to_df(rarr, ["pr", "pet", "apwl", "st", "rech"]).sort_index()
#     return rdf

# # Define the second location of interest by longitude/latitude.
# lon2 = 4.137152
# lat2 = 43.626945

# # Calculate the local recharge condition at this location.
# rdf2 = get_local_recharge(i_date, f_date, lon2, lat2, scale)

# # Resample the resulting pandas dataframe on a yearly basis (sum by year).
# rdf2y = rdf2.resample("Y").sum()
# rdf2y.head()

# # Data Visualization
# fig, ax = plt.subplots(figsize=(15, 6))
# ax.axes.get_yaxis().set_visible(False)

# # Define the x-label locations.
# x = np.arange(len(rdfy))

# # Define the bar width.
# width = 0.25

# # Bar plot associated to groundwater recharge at the 1st location of interest.
# rect1 = ax.bar(
#     x - width / 2, rdfy.rech, width, label="Lyon (France)", color="blue", alpha=0.5
# )

# # Bar plot associated to groundwater recharge at the 2nd location of interest.
# rect2 = ax.bar(
#     x + width / 2,
#     rdf2y.rech,
#     width,
#     label="Montpellier (France)",
#     color="red",
#     alpha=0.5,
# )

# # Define a function to attach a label to each bar.
# def autolabel_recharge(rects):
#     """Attach a text label above each bar in *rects*, displaying its height."""
#     for rect in rects:
#         height = rect.get_height()
#         ax.annotate(
#             "{}".format(int(height)) + " mm",
#             xy=(rect.get_x() + rect.get_width() / 2, height),
#             xytext=(0, 3),  # 3 points vertical offset
#             textcoords="offset points",
#             ha="center",
#             va="bottom",
#             fontsize=8,
#         )

# autolabel_recharge(rect1)
# autolabel_recharge(rect2)

# # Calculate the averaged annual recharge at both locations of interest.
# place1mean = int(rdfy["rech"].mean())
# place2mean = int(rdf2y["rech"].mean())

# # Add an horizontal line associated with averaged annual values (location 1).
# ax.hlines(
#     place1mean,
#     xmin=min(x) - width,
#     xmax=max(x) + width,
#     color="blue",
#     lw=0.5,
#     label="average " + str(place1mean) + " mm/y",
#     alpha=0.5,
# )

# # Add an horizontal line associated with averaged annual values (location 2).
# ax.hlines(
#     place2mean,
#     xmin=min(x) - width,
#     xmax=max(x) + width,
#     color="red",
#     lw=0.5,
#     label="average " + str(place2mean) + " mm/y",
#     alpha=0.5,
# )

# # Add a title.
# ax.set_title("Groundwater recharge comparison between two places", fontsize=12)

# # Define some x/y-axis properties.
# ax.set_xticks(x)
# x_labels = rdfy.index.year.tolist()
# ax.set_xticklabels(x_labels, rotation=45, fontsize=

# 10)

# ax.spines["left"].set_visible(False)
# ax.spines["right"].set_visible(False)
# ax.spines["top"].set_visible(False)

# # Shrink current axis's height by 10% on the bottom.
# box = ax.get_position()
# ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

# # Add a legend below current axis.
# ax.legend(
#     loc="upper center", bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=2
# )

# st.pyplot(fig)
