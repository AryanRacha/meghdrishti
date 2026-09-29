import os
import argparse
from typing import List, Optional
import cdsapi

def download_era5_surface_data(
    output_dir: str,
    year: str,
    month: str,
    days: Optional[List[str]] = None,
    custom_filename: Optional[str] = None
) -> str:
    """
    Downloads real ERA5 Reanalysis data for India bundled into a single monthly chunk.
    Variables: Total Precipitation (tp)
    """
    os.makedirs(output_dir, exist_ok=True)
    c = cdsapi.Client(timeout=600)

    # Bounding Box for India: North 38, West 68, South 8, East 98
    area = [38, 68, 8, 98]

    if days is None:
        # 30 days for April, June, Sept, Nov; 31 for others (Monsoon June/Sept = 30, July/Aug = 31)
        max_days = 30 if month in ["04", "06", "09", "11"] else (
            29 if month == "02" and int(year) % 4 == 0 else (28 if month == "02" else 31)
        )
        days = [f"{d:02d}" for d in range(1, max_days + 1)]

    filename = custom_filename if custom_filename else f"era5_{year}_{month}.nc"
    output_file = os.path.join(output_dir, filename)

    if os.path.exists(output_file):
        print(f"File already exists, skipping: {output_file}")
        return output_file

    print(f"Downloading ERA5 monthly chunk for {year}-{month} ({len(days)} days) -> {output_file}...")

    try:
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': [
                    'total_precipitation',
                ],
                'year': year,
                'month': month,
                'day': days,
                'time': [
                    '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
                    '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
                    '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
                ],
                'area': area,
            },
            output_file
        )
        print(f"Successfully saved: {output_file}")
    except Exception as e:
        print(f"Failed to download {year}-{month}: {e}")
        raise

    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download ERA5 monthly chunks for SIH26081.")
    parser.add_argument("--test", action="store_true", help="Run a 1-day fail-fast test operation")
    args = parser.parse_args()

    print("Starting production data acquisition...")

    if args.test:
        print("--- RUNNING 1-DAY FAIL-FAST TEST ---")
        download_era5_surface_data(
            output_dir="data/raw",
            year="2024",
            month="07",
            days=["15"],
            custom_filename="era5_test.nc"
        )
    else:
        print("--- RUNNING FULL HISTORICAL DATA ACQUISITION (MONTHLY CHUNKS) ---")
        # Target: Prime Monsoon seasons (June - Sept) for 2021, 2022, 2023
        years = ["2021", "2022", "2023"]
        months = ["06", "07", "08", "09"]

        for year in years:
            for month in months:
                # 30 days for June ('06') and Sept ('09'); 31 days for July ('07') and August ('08')
                max_days = 30 if month in ["06", "09"] else 31
                month_days = [f"{d:02d}" for d in range(1, max_days + 1)]

                print(f"\n--- Processing {year}-{month} ({len(month_days)} days) ---")
                download_era5_surface_data(
                    output_dir="data/raw/era5",
                    year=year,
                    month=month,
                    days=month_days
                )

    print("Acquisition script complete. Make sure ~/.cdsapirc is configured properly.")
