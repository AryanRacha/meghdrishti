import os
import boto3
import logging
from botocore import UNSIGNED
from botocore.config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GFSFetcher:
    def __init__(self, output_dir="data/raw/gfs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Use UNSIGNED config to access public AWS buckets without credentials
        self.s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        self.bucket = 'noaa-gfs-bdp-pds'

    def fetch_historical_forecast(self, date_str: str, cycle: str = '00', forecast_hour: int = 24):
        """
        Fetches historical GFS forecast data from NOAA's public AWS S3 bucket.
        date_str: YYYYMMDD
        cycle: '00', '06', '12', '18'
        forecast_hour: Forecast lead time (e.g., 24 for 24-hour ahead forecast)
        """
        # S3 Prefix format: gfs.YYYYMMDD/CC/atmos/gfs.tCCz.pgrb2.0p25.fFFF
        # where CC is cycle (00-18), FFF is forecast hour
        
        # Determine the file key in the bucket
        file_prefix = f"gfs.{date_str}/{cycle}/atmos/gfs.t{cycle}z.pgrb2.0p25.f{forecast_hour:03d}"
        
        local_filename = os.path.join(self.output_dir, f"gfs_{date_str}_{cycle}z_f{forecast_hour:03d}.grib2")
        
        if os.path.exists(local_filename):
            logger.info(f"File {local_filename} already exists. Skipping.")
            return local_filename
            
        logger.info(f"Attempting to download s3://{self.bucket}/{file_prefix}...")
        
        try:
            self.s3.download_file(self.bucket, file_prefix, local_filename)
            logger.info(f"Successfully downloaded to {local_filename}")
            return local_filename
        except Exception as e:
            logger.error(f"Failed to download GFS file: {e}")
            return None

if __name__ == "__main__":
    fetcher = GFSFetcher(output_dir="../../data/raw/gfs")
    # MVP Prototype: Fetch August 1, 2023, 00Z cycle, 24-hour forecast
    # fetcher.fetch_historical_forecast('20230801', '00', 24)
    logger.info("GFSFetcher initialized.")
