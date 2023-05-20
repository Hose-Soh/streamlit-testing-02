import ee
from gwr import ee_utils
import geemap.foliumap as geemap



def get_precipitation_data_for_dates(start_date, end_date):
    return (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
            .select("precipitation")
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    )


def get_potential_evaporation_for_dates(start_date, end_date):
    # Import potential evaporation PET and its quality indicator ET_QC.
    return (
        ee.ImageCollection("MODIS/006/MOD16A2")
            .select(["PET", "ET_QC"])
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    )


def get_mean_monthly_meteorological_data(start_date, end_date):
    """
    Returns an ImageCollection that combines the Precipitation and Potential Evaporation data
    for a region across a time period resampled to provide monthly mean values
    """
    
    pr = get_precipitation_data_for_dates(start_date, end_date)
    pet = get_potential_evaporation_for_dates(start_date, end_date)

    # Apply the resampling function to the precipitation dataset.
    pr_m = ee_utils.sum_resampler(pr, 1, "month", 1, "pr")

    # Apply the resampling function to the PET dataset.
    pet_m = ee_utils.sum_resampler(pet.select("PET"), 1, "month", 0.0125, "pet")

    # Combine precipitation and evapotranspiration.
    meteo = pr_m.combine(pet_m)

    
    return meteo



def get_mean_monthly_meteorological_data_for_roi_df(roi, scale, meteoImageCollection, ):
    # Import meteorological data as an array at the location of interest.
    meteo_arr = meteoImageCollection.getRegion(roi, scale).getInfo()

    # Transform the array into a pandas dataframe and sort the index.
    # Data for ROI may have multiple sample points within ROI for a date so group by date and take the mean
    # To avoid loosing the datetime and time fields (used elswhere), group by both then remove time from the index
    meteo_df = ee_utils.ee_array_to_df(meteo_arr, ["pr", "pet"]).groupby(['datetime', 'time']).mean(
        ['pr', 'pet']).sort_values("datetime")
    meteo_df.reset_index(level='time', inplace=True)
    meteo_df.rename(columns={'pr': 'mean-pr'}, inplace=True)
    meteo_df.rename(columns={'pet': 'mean-pet'}, inplace=True)
    meteo_df["date"] = meteo_df.index.strftime("%m-%Y")

    return meteo_df



