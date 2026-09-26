import os
import cdsapi
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ERA5Fetcher:
    def __init__(self, output_dir="data/raw/era5"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # CDS API requires ~/.cdsapirc file with url and key to be set.
        try:
            self.client = cdsapi.Client()
        except Exception as e:
            logger.warning(f"Could not initialize CDS API Client. Ensure ~/.cdsapirc is configured. Error: {e}")
            self.client = None

    def fetch_monthly_rainfall(self, year: int, month: int):
        """
        Fetches hourly total precipitation for a specific month.
        Bounding box restricted to Indian subcontinent (approx):
        North: 38, West: 68, South: 8, East: 98
        """
        if not self.client:
            logger.error("CDS API client not initialized. Cannot fetch data.")
            return None

        filename = os.path.join(self.output_dir, f"era5_tp_india_{year}_{month:02d}.nc")
        if os.path.exists(filename):
            logger.info(f"File {filename} already exists. Skipping download.")
            return filename

        logger.info(f"Requesting ERA5 data for {year}-{month:02d}...")
        
        try:
            self.client.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': 'reanalysis',
                    'variable': [
                        'total_precipitation',
                    ],
                    'year': str(year),
                    'month': f"{month:02d}",
                    'day': [f"{d:02d}" for d in range(1, 32)],
                    'time': [f"{h:02d}:00" for h in range(24)],
                    'area': [38, 68, 8, 98], # N, W, S, E
                    'format': 'netcdf',
                },
                filename
            )
            logger.info(f"Successfully downloaded to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to fetch ERA5 data: {e}")
            return None

if __name__ == "__main__":
    fetcher = ERA5Fetcher(output_dir="../../data/raw/era5")
    # For MVP prototype, fetch August 2023 (Active monsoon month)
    # fetcher.fetch_monthly_rainfall(2023, 8)
    logger.info("ERA5Fetcher initialized. Run with valid .cdsapirc to download data.")
