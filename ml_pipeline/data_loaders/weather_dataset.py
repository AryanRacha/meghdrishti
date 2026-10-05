import os
import torch
import xarray as xr
import numpy as np
from torch.utils.data import Dataset
import logging
import math
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductionWeatherDataset(Dataset):
    def __init__(self, data_dir, dates, target_shape=(320, 320)):
        self.data_dir = data_dir
        self.dates = dates
        
        # Indian BBox V2: 6°–38°N, 66°–98°E (Exactly 32x32 degrees)
        # Upscaled to 320x320 for IMD 0.1° target resolution super-resolution
        self.target_lats = np.linspace(38, 6, target_shape[0])
        self.target_lons = np.linspace(66, 98, target_shape[1])
        self.target_shape = target_shape

    def __len__(self):
        return len(self.dates)

    def _normalize_zscore(self, tensor):
        mean = tensor.mean()
        std = tensor.std()
        return (tensor - mean) / (std + 1e-8)

    def _normalize_minmax(self, tensor, min_val=0.0, max_val=100.0):
        # Used for bounded physical variables like Relative Humidity
        tensor_clamped = torch.clamp(tensor, min=min_val, max=max_val)
        return (tensor_clamped - min_val) / (max_val - min_val)

    def _get_temporal_embeddings(self, date_str, lead_time_hours=24.0):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_of_year = dt.timetuple().tm_yday
        
        # Sinusoidal encoding for seasonality
        sin_day = math.sin(2 * math.pi * day_of_year / 365.25)
        cos_day = math.cos(2 * math.pi * day_of_year / 365.25)
        
        return torch.tensor([lead_time_hours, sin_day, cos_day], dtype=torch.float32)

    def __getitem__(self, idx):
        date = self.dates[idx] # '2023-08-01'
        year, month, day = date.split('-')
        
        # In V2, we expect raw data processing rather than the old preprocessed .pt files,
        # because the channel structure and resolution changed completely.
        # To prevent crashing if real data isn't downloaded yet, we will mock missing channels.
        
        raw_dir = self.data_dir.replace('processed', 'raw')
        era5_path = os.path.join(raw_dir, 'era5', f'era5_{year}_{month}.nc')
        
        date_str_no_hyphen = date.replace('-', '')
        gfs_path = os.path.join(raw_dir, 'gfs', f'gfs_{date_str_no_hyphen}_00z_f024.grib2')
        ai_path = os.path.join(raw_dir, 'ai', f'pangu_{year}_{month}_{day}.nc') # Expected format
        
        # Mock load logic for V2 transition 
        # (Replace with real NetCDF/GRIB2 loading when data is ready)
        
        def safe_load_or_mock(path, var_names, is_grib=False):
            # If file doesn't exist, return zeros to allow the pipeline to test-run
            if not os.path.exists(path):
                return [torch.zeros(self.target_shape, dtype=torch.float32) for _ in var_names]
            
            try:
                if is_grib:
                    import cfgrib
                    datasets = cfgrib.open_datasets(path)
                else:
                    datasets = [xr.open_dataset(path)]
            except Exception:
                return [torch.zeros(self.target_shape, dtype=torch.float32) for _ in var_names]
                
            tensors = []
            for v in var_names:
                tensor_found = torch.zeros(self.target_shape, dtype=torch.float32)
                for ds in datasets:
                    # Upscale to 320x320 using nearest or bilinear
                    ds_interp = ds.interp(latitude=self.target_lats, longitude=self.target_lons, method='nearest')
                    matched = [key for key in ds_interp.data_vars if v.split('_')[0] in key.lower()]
                    if matched:
                        tensor_found = torch.tensor(ds_interp[matched[0]].values, dtype=torch.float32)
                        break
                tensors.append(tensor_found)
                
            for ds in datasets:
                ds.close()
            return tensors

        # Ground Truth Targets
        target_vars = safe_load_or_mock(era5_path, ['tp', 't2m', 'u10', 'v10', 'z'])
        t_rain = target_vars[0] * 1000.0 # Convert to mm
        t_temp = target_vars[1]
        t_u = target_vars[2]
        t_v = target_vars[3]
        dem = target_vars[4] / 9.80665

        # GFS Variables (Rain, Temp, U, V, MSLP, RH)
        gfs_vars = safe_load_or_mock(gfs_path, ['tp', 't2m', 'u10', 'v10', 'msl', 'r'], is_grib=True)
        gfs_rain, gfs_temp, gfs_u, gfs_v, gfs_mslp, gfs_rh = gfs_vars

        # AI Proxy Variables (Rain, Temp, U, V, MSLP, RH)
        ai_vars = safe_load_or_mock(ai_path, ['tp', 't2m', 'u10', 'v10', 'msl', 'r'])
        ai_rain, ai_temp, ai_u, ai_v, ai_mslp, ai_rh = ai_vars

        # --- Stack Inputs (13 Channels) ---
        inputs = torch.stack([
            self._normalize_zscore(gfs_rain),
            self._normalize_zscore(gfs_temp),
            self._normalize_zscore(gfs_u),
            self._normalize_zscore(gfs_v),
            self._normalize_zscore(gfs_mslp),
            self._normalize_minmax(gfs_rh), # Bounded RH
            
            self._normalize_zscore(ai_rain),
            self._normalize_zscore(ai_temp),
            self._normalize_zscore(ai_u),
            self._normalize_zscore(ai_v),
            self._normalize_zscore(ai_mslp),
            self._normalize_minmax(ai_rh), # Bounded RH
            
            self._normalize_zscore(dem)
        ], dim=0)

        # Temporal Condition [LeadTime, Sin(Day), Cos(Day)]
        condition = self._get_temporal_embeddings(date)

        # Forecasts to Blend [Models, H, W]
        f_rain = torch.stack([gfs_rain, ai_rain], dim=0)
        f_temp = torch.stack([gfs_temp, ai_temp], dim=0)
        f_u = torch.stack([gfs_u, ai_u], dim=0)
        f_v = torch.stack([gfs_v, ai_v], dim=0)
        
        # Targets
        targets = (t_rain.unsqueeze(0), t_temp.unsqueeze(0), t_u.unsqueeze(0), t_v.unsqueeze(0))
        forecasts = (f_rain, f_temp, f_u, f_v)

        return inputs, condition, forecasts, targets
