import streamlit as st

st.set_page_config(page_title="Soil Data Exploration")

# Add title to page
st.title("Explore Soil Characteristics and Hydrological Properties of a Region")

with st.sidebar:
    # Create two columns
    col1, col2 = st.columns(2)
    logo_omdena = "./resources/omdena.png"
    logo_nitrolytics = "./resources/nitrolytics.png"
    # Display the first logo image in the first column with no margin
    col1.image(logo_omdena, width=100, use_column_width=False)

    # Display the second logo image in the second column with no margin
    col2.image(logo_nitrolytics, width=100, use_column_width=False)