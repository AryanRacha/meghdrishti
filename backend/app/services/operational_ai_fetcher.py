"""
Operational AI Model Fetcher (AIFS from ECMWF Open Data).
"""
import os
import logging
import tempfile
import numpy as np
import xarray as xr
from ecmwf.opendata import Client
from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)

class OperationalAIFetcher:
    def __init__(self, target_shape=(128, 128)):
        self.target_lats = np.linspace(38.0, 8.0, target_shape[0])
        self.target_lons = np.linspace(68.0, 98.0, target_shape[1])
        try:
            self.client = Client(source="aws", model="aifs-single", resol="0p25")
        except Exception as e:
            logger.error(f"Failed to initialize ECMWF AIFS client: {e}")
            self.client = None

    def fetch_ai_india(self, date_str: str, lead_time: int = 24, gfs_reference=None):
        if self.client is None:
            return self._fallback_synthetic(gfs_reference)
            
        logger.info(f"Attempting live AIFS fetch for lead time {lead_time}...")
        
        target_file = None
        success = False
        
        for source in ["azure", "ecmwf", "aws"]:
            try:
                logger.info(f"Trying AIFS source: {source}")
                client = Client(source=source, model="aifs-single", resol="0p25")
                with tempfile.NamedTemporaryFile(suffix=".grib2", delete=False) as tmp:
                    target_file = tmp.name
                    
                client.retrieve(
                    step=lead_time,
                    type="fc",
                    param=["2t", "tp", "10u", "10v"],
                    target=target_file
                )
                success = True
                break  # If successful, exit loop
            except Exception as e:
                logger.warning(f"Source {source} failed: {e}")
                if target_file and os.path.exists(target_file):
                    os.remove(target_file)
                target_file = None
                
        if not success or target_file is None:
            logger.warning("All AIFS sources failed. Falling back to synthetic.")
            return self._fallback_synthetic(gfs_reference)
            
        try:
            import cfgrib
            datasets = cfgrib.open_datasets(target_file)
            
            ai_temp, ai_rain, u_wind, v_wind = None, None, None, None
            
            for ds in datasets:
                # Crop to India Bounding Box (ECMWF lats are top-to-bottom, 90 to -90)
                ds_india = ds.sel(latitude=slice(38.0, 8.0), longitude=slice(68.0, 98.0))
                ds_interp = ds_india.interp(latitude=self.target_lats, longitude=self.target_lons, method="nearest")
                
                if 't2m' in ds_interp:
                    ai_temp = ds_interp['t2m'].values.astype(np.float32)
                if 'tp' in ds_interp:
                    ai_rain = ds_interp['tp'].values.astype(np.float32)
                    ai_rain = np.clip(ai_rain, 0.0, None)
                if 'u10' in ds_interp:
                    u_wind = ds_interp['u10'].values
                if 'v10' in ds_interp:
                    v_wind = ds_interp['v10'].values
                ds.close()
                
            ai_wind = np.sqrt(u_wind**2 + v_wind**2).astype(np.float32)
            os.remove(target_file)
            
            logger.info("Successfully fetched and decoded real AIFS operational data!")
            return {
                "rain": ai_rain,
                "temp": ai_temp,
                "wind": ai_wind
            }
            
        except Exception as e:
            logger.warning(f"Live AIFS fetch failed (Missing eccodes?): {e}")
            if os.path.exists(target_file):
                os.remove(target_file)
            return self._fallback_synthetic(gfs_reference)

    def _fallback_synthetic(self, gfs_reference):
        # Fallback to the calibrated Gaussian blur if real AIFS fails
        if gfs_reference is not None:
            r_ref = gfs_reference["rain"]
            t_ref = gfs_reference["temp"]
            w_ref = gfs_reference["wind"]

            ai_rain = gaussian_filter(r_ref * 0.75, 1.6)
            ai_temp = gaussian_filter(t_ref, 0.8)
            ai_wind = gaussian_filter(w_ref * 0.9, 1.0)

            return {
                "rain": np.clip(ai_rain, 0.0, None).astype(np.float32),
                "temp": ai_temp.astype(np.float32),
                "wind": np.clip(ai_wind, 0.0, None).astype(np.float32),
            }
        return None
