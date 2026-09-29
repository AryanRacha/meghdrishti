import os
import glob
import xarray as xr
import numpy as np

def calibrate_extremes(data_dir):
    """
    Computes statistical percentiles for the true ERA5 Indian precipitation dataset.
    This informs the 'alpha' and 'beta' tuning in the Continuous Power-Law loss function.
    """
    print(f"Scanning for NetCDF files in {data_dir}...")
    nc_files = glob.glob(os.path.join(data_dir, "*.nc"))

    if not nc_files:
        raise FileNotFoundError(f"No .nc files found in {data_dir}. Run download script first.")

    all_precip = []

    for f in nc_files:
        try:
            ds = xr.open_dataset(f)
            # ERA5 total_precipitation is usually in meters, convert to mm for practical usage
            tp_mm = ds['tp'].values * 1000.0
            all_precip.append(tp_mm.flatten())
            ds.close()
        except Exception as e:
            print(f"Error reading {f}: {e}")

    if not all_precip:
        print("No valid data loaded.")
        return

    print("Concatenating spatial grids for statistical analysis...")
    full_array = np.concatenate(all_precip)

    # Filter out dry pixels
    wet_array = full_array[full_array > 1.0]

    print("\n--- STATISTICAL CALIBRATION (WET PIXELS > 1mm) ---")
    print(f"Total Wet Pixels Analyzed: {len(wet_array):,}")

    if len(wet_array) == 0:
        print("No rain detected in dataset.")
        return

    p90 = np.percentile(wet_array, 90)
    p95 = np.percentile(wet_array, 95)
    p99 = np.percentile(wet_array, 99)

    print(f"90th Percentile (Heavy Rain):   {p90:.2f} mm")
    print(f"95th Percentile (Very Heavy):   {p95:.2f} mm")
    print(f"99th Percentile (Extreme Event):{p99:.2f} mm")

    print("\n--- RECOMMENDED LOSS PARAMETERS ---")
    print("For ContinuousExtremeWeightedMSELoss:")
    print("Set alpha so that penalty becomes significant around the 90th percentile.")
    print("Set beta (e.g. 2.0 or 3.0) to aggressively scale up towards the 99th percentile.")

if __name__ == "__main__":
    target_dir = "../data/raw/era5"
    if os.path.exists(target_dir):
        calibrate_extremes(target_dir)
    else:
        print(f"Data directory {target_dir} does not exist.")
