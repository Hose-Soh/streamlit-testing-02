import ee
from gwr import ee_utils
import pandas as pd


def get_smap_soil_moisture_for_dates(start_date, end_date):
    return (
        ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture")
            .select(["ssm", "susm"])
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    )


def get_mean_monthly_smap_data(start_date, end_date):
    """
    Returns an ImageCollection that combines the SMAP soil moisture data for a region
    across a time period resampled to provide monthly mean values.
    """
    smap = get_smap_soil_moisture_for_dates(start_date, end_date)

    # Apply the resampling function to the SMAP soil moisture dataset.
    smap_m = ee_utils.sum_resampler(smap, 1, "month", 1, ["ssm", "susm"])

    return smap_m


def get_mean_monthly_smap_data_for_roi_df(roi, scale, smapImageCollection):
    # Import SMAP soil moisture data as an array at the location of interest.
    smap_arr = smapImageCollection.getRegion(roi, scale).getInfo()

    # Transform the array into a pandas DataFrame and sort the index.
    # Data for the ROI may have multiple sample points within ROI for a date, so group by date and take the mean.
    # To avoid losing the datetime and time fields (used elsewhere), group by both and then remove time from the index.
    smap_df = ee_utils.ee_array_to_df(smap_arr, ["ssm", "susm"]).groupby(['datetime', 'time']).mean().sort_values(
        "datetime")
    smap_df.reset_index(level='time', inplace=True)
    smap_df.rename(columns={'ssm': 'mean-ssm', 'susm': 'mean-susm'}, inplace=True)
    smap_df["date"] = smap_df.index.strftime("%m-%Y")

    return smap_df


def get_combined_dataframe(start_date, end_date, roi, scale):
    # Retrieve the SMAP soil moisture ImageCollection for the specified date range
    smap_collection = get_smap_soil_moisture_for_dates(start_date, end_date)

    # Get the monthly mean SMAP data for the ROI as separate DataFrames
    smap_ssm = get_mean_monthly_smap_data_for_roi_df(roi, scale, smap_collection.select("ssm"))
    smap_susm = get_mean_monthly_smap_data_for_roi_df(roi, scale, smap_collection.select("susm"))

    # Merge the two DataFrames based on the common date column
    combined_df = pd.merge(smap_ssm, smap_susm, on="date")

    return combined_df
