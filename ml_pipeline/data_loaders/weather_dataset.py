import os
import torch
import xarray as xr
import numpy as np
from torch.utils.data import Dataset

class ProductionWeatherDataset(Dataset):
    def __init__(self, data_dir, dates, stats_dict, target_shape=(128, 128)):
        """
        Production dataset for SIH26081.
        Strict loading without mock fallbacks.

        Args:
            data_dir (str): Path to processed data.
            dates (list): List of date strings (e.g., '2023-01-01').
            stats_dict (dict): Dictionary containing means and stds for normalization.
                               e.g. {'gfs': (mean, std), 'ai': (mean, std), 'dem': (mean, std), 'lead': (mean, std)}
            target_shape (tuple): (H, W) for spatial interpolation.
        """
        self.data_dir = data_dir
        self.dates = dates
        self.stats = stats_dict

        # Indian Bounding Box: Lat 8 to 38, Lon 68 to 98
        self.target_lats = np.linspace(38, 8, target_shape[0])  # North to South usually
        self.target_lons = np.linspace(68, 98, target_shape[1]) # West to East

    def __len__(self):
        return len(self.dates)

    def _normalize(self, tensor, key):
        mean, std = self.stats[key]
        return (tensor - mean) / (std + 1e-8)

    def __getitem__(self, idx):
        date = self.dates[idx]

        # Paths for specific date (assuming naming convention)
        gfs_path = os.path.join(self.data_dir, 'gfs', f'gfs_{date}.nc')
        ai_path = os.path.join(self.data_dir, 'ai', f'ai_{date}.nc')
        dem_path = os.path.join(self.data_dir, 'dem', 'dem_india.nc') # Static
        era5_path = os.path.join(self.data_dir, 'era5', f'era5_{date}.nc')

        # Hard fail if missing
        for p in [gfs_path, ai_path, dem_path, era5_path]:
            if not os.path.exists(p):
                raise FileNotFoundError(f"Missing required production data file: {p}")

        # Load datasets (using xarray and netCDF4 backend)
        ds_gfs = xr.open_dataset(gfs_path)
        ds_ai = xr.open_dataset(ai_path)
        ds_dem = xr.open_dataset(dem_path)
        ds_era5 = xr.open_dataset(era5_path)

        # Strict Spatial Interpolation to exact Indian BBox grid
        # This resolves any resolution or coordinate mismatches instantly
        ds_gfs = ds_gfs.interp(latitude=self.target_lats, longitude=self.target_lons, method='nearest')
        ds_ai = ds_ai.interp(latitude=self.target_lats, longitude=self.target_lons, method='nearest')
        ds_dem = ds_dem.interp(latitude=self.target_lats, longitude=self.target_lons, method='nearest')
        ds_era5 = ds_era5.interp(latitude=self.target_lats, longitude=self.target_lons, method='nearest')

        # Extract variables as tensors (assuming 'tp' for total precipitation, 'elevation' for DEM)
        # ERA5 'tp' is often in meters, GFS might be mm/kg/m^2. Assume pre-processing standardized them to mm.
        gfs_tp = torch.tensor(ds_gfs['tp'].values, dtype=torch.float32)
        ai_tp = torch.tensor(ds_ai['tp'].values, dtype=torch.float32)
        dem = torch.tensor(ds_dem['elevation'].values, dtype=torch.float32)

        # For Lead Time, we assume it's a fixed feature for this specific sample
        # (e.g., day 1 forecast). We'll create a constant channel for it.
        lead_time_val = 24.0
        lead_time_ch = torch.full_like(gfs_tp, lead_time_val)

        # Get target Ground Truth
        target_tp = torch.tensor(ds_era5['tp'].values, dtype=torch.float32)

        # Apply strict Z-score standardization
        gfs_tp_norm = self._normalize(gfs_tp, 'gfs')
        ai_tp_norm = self._normalize(ai_tp, 'ai')
        dem_norm = self._normalize(dem, 'dem')
        lead_time_norm = self._normalize(lead_time_ch, 'lead_time')

        # Stack inputs into [4, H, W] tensor
        inputs = torch.stack([gfs_tp_norm, ai_tp_norm, dem_norm, lead_time_norm], dim=0)

        # Forecasts shape should be [2, H, W] for the loss function weighting
        forecasts = torch.stack([gfs_tp, ai_tp], dim=0)

        # Targets shape should be [1, H, W]
        target = target_tp.unsqueeze(0)

        # Close xarray datasets
        ds_gfs.close()
        ds_ai.close()
        ds_dem.close()
        ds_era5.close()

        return inputs, forecasts, target

if __name__ == '__main__':
    print("Production dataset structure ready.")
