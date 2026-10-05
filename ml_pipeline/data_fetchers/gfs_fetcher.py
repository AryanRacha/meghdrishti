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
        self.s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED, max_pool_connections=50))
        self.bucket = 'noaa-gfs-bdp-pds'

    def fetch_historical_forecast(self, date_str: str, cycle: str = '00', forecast_hour: int = 24):
        """
        Fetches historical GFS forecast data from NOAA's public AWS S3 bucket.
        Handles the NOAA directory restructure (pre-2021 vs post-2021).
        """
        local_filename = os.path.join(self.output_dir, f"gfs_{date_str}_{cycle}z_f{forecast_hour:03d}.grib2")

        if os.path.exists(local_filename):
            return local_filename

        # NOAA changed their S3 directory structure in March 2021.
        # Post-March 2021: gfs.YYYYMMDD/CC/atmos/gfs.tCCz.pgrb2.0p25.fFFF
        # Pre-March 2021:  gfs.YYYYMMDD/CC/gfs.tCCz.pgrb2.0p25.fFFF
        paths_to_try = [
            f"gfs.{date_str}/{cycle}/atmos/gfs.t{cycle}z.pgrb2.0p25.f{forecast_hour:03d}",
            f"gfs.{date_str}/{cycle}/gfs.t{cycle}z.pgrb2.0p25.f{forecast_hour:03d}",
        ]

        for file_prefix in paths_to_try:
            try:
                self.s3.download_file(self.bucket, file_prefix, local_filename)
                logger.info(f"Downloaded {local_filename}")
                return local_filename
            except Exception:
                continue

        logger.warning(f"GFS not found on AWS for {date_str}. Skipping.")
        return None
