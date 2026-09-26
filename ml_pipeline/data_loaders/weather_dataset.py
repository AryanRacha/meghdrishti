import os
import torch
from torch.utils.data import Dataset
import numpy as np
import logging

try:
    import xarray as xr
    XARRAY_AVAILABLE = True
except ImportError:
    XARRAY_AVAILABLE = False

logger = logging.getLogger(__name__)

class RealWeatherGridDataset(Dataset):
    """
    PyTorch Dataset that loads real NetCDF/GRIB2 files for training the U-Net.
    Falls back to mock data if the files are not found or xarray is missing, 
    ensuring the training loop never breaks during prototyping.
    """
    def __init__(self, gfs_dir='data/raw/gfs', era5_dir='data/raw/era5', grid_size=(128, 128), n_samples=100):
        self.gfs_dir = gfs_dir
        self.era5_dir = era5_dir
        self.grid_size = grid_size
        self.n_samples = n_samples
        
        self.gfs_files = []
        if os.path.exists(self.gfs_dir):
            self.gfs_files = [os.path.join(self.gfs_dir, f) for f in os.listdir(self.gfs_dir) if f.endswith('.grib2') or f.endswith('.nc')]
            
        logger.info(f"Found {len(self.gfs_files)} real GFS files in {self.gfs_dir}.")

    def __len__(self):
        return self.n_samples

    def _get_mock_data(self):
        # Fallback to mock arrays if data isn't downloaded yet
        base_rain = np.random.rand(*self.grid_size) * 100.0
        gfs_rain = base_rain + np.random.randn(*self.grid_size) * 10.0
        ai_rain = base_rain + np.random.randn(*self.grid_size) * 5.0
        
        dem = np.linspace(0, 1, self.grid_size[0]*self.grid_size[1]).reshape(self.grid_size)
        lead_time = np.ones(self.grid_size) * np.random.rand()
        
        input_tensor = np.stack([gfs_rain, ai_rain, dem, lead_time], axis=0)
        
        era5_target = base_rain + np.random.randn(*self.grid_size) * 2.0
        if np.random.rand() > 0.8:
            era5_target[10:20, 10:20] += 80.0
            
        era5_target = np.clip(era5_target, 0, None)
        target_tensor = np.expand_dims(era5_target, axis=0)
        forecast_tensor = np.stack([gfs_rain, ai_rain], axis=0)
        
        return (
            torch.tensor(input_tensor, dtype=torch.float32), 
            torch.tensor(forecast_tensor, dtype=torch.float32), 
            torch.tensor(target_tensor, dtype=torch.float32)
        )

    def __getitem__(self, idx):
        # If we have real data and xarray, let's load it!
        if XARRAY_AVAILABLE and len(self.gfs_files) > 0:
            try:
                # Pick a random real file for now (in a real scenario, idx would map to a specific date)
                gfs_file = self.gfs_files[idx % len(self.gfs_files)]
                
                # Load via xarray
                # Note: cfgrib required for .grib2 files
                ds_gfs = xr.open_dataset(gfs_file, engine='cfgrib' if gfs_file.endswith('.grib2') else 'netcdf4')
                
                # Extract precipitation variable (commonly 'tp' or 'prate' in GFS)
                # For this prototype, we'll try to find a rainfall variable, or fallback to mock
                var_name = [v for v in ds_gfs.data_vars if 'precip' in v.lower() or v in ['tp', 'prate']]
                if var_name:
                    rain_data = ds_gfs[var_name[0]].values
                    
                    # Resize to self.grid_size (simplified cropping/padding for MVP)
                    # Real implementation uses regrid.py
                    h, w = rain_data.shape[-2:]
                    h_idx = min(h, self.grid_size[0])
                    w_idx = min(w, self.grid_size[1])
                    
                    gfs_rain = np.zeros(self.grid_size)
                    gfs_rain[:h_idx, :w_idx] = rain_data[:h_idx, :w_idx]
                    
                    # Mock the AI forecast and Target since we only downloaded GFS for now
                    ai_rain = gfs_rain + np.random.randn(*self.grid_size) * 5.0
                    dem = np.zeros(self.grid_size)
                    lead_time = np.ones(self.grid_size) * 0.5
                    
                    input_tensor = np.stack([gfs_rain, ai_rain, dem, lead_time], axis=0)
                    target_tensor = np.expand_dims(gfs_rain + np.random.randn(*self.grid_size), axis=0)
                    forecast_tensor = np.stack([gfs_rain, ai_rain], axis=0)
                    
                    return (
                        torch.tensor(input_tensor, dtype=torch.float32), 
                        torch.tensor(forecast_tensor, dtype=torch.float32), 
                        torch.tensor(target_tensor, dtype=torch.float32)
                    )
            except Exception as e:
                logger.warning(f"Failed to load real data: {e}. Falling back to mock.")
                
        # Fallback
        return self._get_mock_data()

if __name__ == '__main__':
    dataset = RealWeatherGridDataset(gfs_dir='../../data/raw/gfs', era5_dir='../../data/raw/era5')
    inputs, forecasts, targets = dataset[0]
    print(f"Inputs shape: {inputs.shape}")
    print(f"Forecasts shape: {forecasts.shape}")
    print(f"Targets shape: {targets.shape}")
