import cdsapi
import os
import argparse

def download_era5_surface_data(output_dir, year, month, days, custom_filename=None):
    """
    Downloads real ERA5 Reanalysis data for India.
    Variables: Total Precipitation (tp)
    """
    os.makedirs(output_dir, exist_ok=True)
    c = cdsapi.Client()

    # Bounding Box for India: North 38, West 68, South 8, East 98
    area = [38, 68, 8, 98]

    for day in days:
        if custom_filename:
            output_file = os.path.join(output_dir, custom_filename)
        else:
            output_file = os.path.join(output_dir, f"era5_{year}-{month}-{day}.nc")

        print(f"Downloading ERA5 data for {year}-{month}-{day}...")

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
                    'day': day,
                    'time': [
                        '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
                        '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                        '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
                        '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
                    ],
                    'area': area,
                },
                output_file)
            print(f"Saved: {output_file}")
        except Exception as e:
            print(f"Failed to download {year}-{month}-{day}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download ERA5 data for SIH26081.")
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
        print("--- RUNNING FULL HISTORICAL DATA ACQUISITION ---")
        # Target: Monsoon seasons (June - Sept) for recent years
        years = ["2021", "2022", "2023"]
        months = ["06", "07", "08", "09"]
        days = [f"{d:02d}" for d in range(1, 32)] # 01 to 31

        for year in years:
            for month in months:
                # Limit days to 30 for June/Sept to avoid API errors on day 31
                month_days = days if month not in ["06", "09"] else days[:-1]

                print(f"\n--- Processing {year}-{month} ---")
                download_era5_surface_data(
                    output_dir="data/raw/era5",
                    year=year,
                    month=month,
                    days=month_days
                )

    print("Acquisition script complete. Make sure ~/.cdsapirc is configured properly.")
