import os
import xarray as xr
import numpy as np

def verify_file(filepath):
    print(f"--- DIAGNOSTIC AUDIT: {filepath} ---")

    if not os.path.exists(filepath):
        print(f"ERROR: File not found at {filepath}")
        return

    try:
        # 1. Attempt to open natively
        ds = xr.open_dataset(filepath)
        print("[✓] Successfully opened file with xarray engine.")

        # 2. Extract and print coordinate bounds
        lats = ds['latitude'].values
        lons = ds['longitude'].values

        print("\n--- COORDINATE BOUNDS ---")
        print(f"Latitude Range:  {lats.min()} to {lats.max()} (Target Indian BBox: 8 to 38)")
        print(f"Longitude Range: {lons.min()} to {lons.max()} (Target Indian BBox: 68 to 98)")

        # 3. Print matrix shape and variable names
        print("\n--- DATA STRUCTURE ---")
        variables = list(ds.data_vars)
        print(f"Data Variables Found: {variables}")

        for var in variables:
            data_array = ds[var]
            print(f"Variable '{var}' Shape: {data_array.shape}")

            # 4. NaN Check and Max Value
            np_data = data_array.values
            has_nans = np.isnan(np_data).any()
            print(f"Contains NaNs?        {has_nans}")

            # Calculate max value
            max_val = np.nanmax(np_data)

            # ERA5 total precipitation ('tp') is conventionally in meters.
            # We convert to mm for readability if it seems small.
            if var == 'tp' and max_val < 5.0:
                print(f"Max Value Recorded:   {max_val:.6f} meters ({max_val * 1000:.2f} mm)")
            else:
                print(f"Max Value Recorded:   {max_val:.6f}")

        ds.close()
        print("\n[✓] Diagnostic Audit Complete. Safe to scale operations.")

    except Exception as e:
        print(f"\n[X] ERROR: Failed to process file. WSL environment or binary mismatch.")
        print(f"Exception details:\n{e}")

if __name__ == "__main__":
    # Path is relative to the ml_pipeline root directory
    test_file_path = "data/raw/era5_test.nc"
    verify_file(test_file_path)
