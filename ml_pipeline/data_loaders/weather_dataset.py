import os
import torch
import xarray as xr
import numpy as np
from torch.utils.data import Dataset
import logging

logger = logging.getLogger(__name__)

class ProductionWeatherDataset(Dataset):
    def __init__(self, data_dir, dates, target_shape=(128, 128)):
        self.data_dir = data_dir
        self.dates = dates
        
        # Indian BBox
        self.target_lats = np.linspace(38, 8, target_shape[0])
        self.target_lons = np.linspace(68, 98, target_shape[1])
        self.target_shape = target_shape

    def __len__(self):
        return len(self.dates)

    def _normalize(self, tensor):
        # Basic dynamic Z-score normalization for the batch
        mean = tensor.mean()
        std = tensor.std()
        return (tensor - mean) / (std + 1e-8)

    def __getitem__(self, idx):
        date = self.dates[idx] # '2023-08-01'
        year, month, day = date.split('-')
        
        # --- Lightning Fast Preprocessed Load ---
        processed_path = f'data/processed/{date}.pt'
        if os.path.exists(processed_path):
            data = torch.load(processed_path, weights_only=True)
            gfs_rain, gfs_temp, gfs_wind_mag = data['gfs']
            ai_rain, ai_temp, ai_wind_mag = data['ai']
            t_rain, t_temp, t_wind = data['target']
            dem = data['dem']
            
            inputs = torch.stack([
                self._normalize(gfs_rain), self._normalize(gfs_temp), self._normalize(gfs_wind_mag),
                self._normalize(ai_rain), self._normalize(ai_temp), self._normalize(ai_wind_mag),
                self._normalize(dem)
            ], dim=0) # 7 Channels
            
            lead_time = torch.tensor([24.0], dtype=torch.float32)
            f_rain = torch.stack([gfs_rain, ai_rain], dim=0)
            f_temp = torch.stack([gfs_temp, ai_temp], dim=0)
            f_wind = torch.stack([gfs_wind_mag, ai_wind_mag], dim=0)
            
            return inputs, lead_time, (f_rain, f_temp, f_wind), (t_rain.unsqueeze(0), t_temp.unsqueeze(0), t_wind.unsqueeze(0))
        
        raw_dir = self.data_dir.replace('processed', 'raw')
        era5_path = os.path.join(raw_dir, 'era5', f'era5_{year}_{month}.nc')
        
        date_str_no_hyphen = date.replace('-', '')
        gfs_path = os.path.join(raw_dir, 'gfs', f'gfs_{date_str_no_hyphen}_00z_f024.grib2')
        ai_path = os.path.join(raw_dir, 'ai', f'graphcast_{year}_{month}.nc') # GraphCast downloaded monthly
        
        # --- 1. Load ERA5 Targets and DEM ---
        if not os.path.exists(era5_path):
            raise FileNotFoundError(f"Missing ERA5 target data: {era5_path}")
        
        ds_era5 = xr.open_dataset(era5_path)
        day_data = ds_era5.sel(valid_time=slice(f"{date} 00:00:00", f"{date} 23:59:59")).mean(dim='valid_time')
        day_data = day_data.interp(latitude=self.target_lats, longitude=self.target_lons, method='nearest')
        
        if 'tp' in day_data:
            target_rain = torch.tensor(day_data['tp'].values, dtype=torch.float32) * 1000.0 # Convert to mm
        else:
            # Fallback if Copernicus CDS API omitted precipitation
            target_rain = torch.zeros(self.target_shape, dtype=torch.float32)
            
        target_temp = torch.tensor(day_data['t2m'].values, dtype=torch.float32)
        target_wind_u = torch.tensor(day_data['u10'].values, dtype=torch.float32)
        target_wind_v = torch.tensor(day_data['v10'].values, dtype=torch.float32)
        target_wind_mag = torch.sqrt(target_wind_u**2 + target_wind_v**2) # Magnitude for blending
        
        # If 'z' (geopotential) is available, use it as DEM, otherwise mock it for prototype testing
        dem = torch.tensor(day_data['z'].values / 9.80665, dtype=torch.float32) if 'z' in day_data else torch.zeros(self.target_shape)
        ds_era5.close()

        # --- 2. Load Forecast Models (Strict) ---
        def load_strict(path, var_names, is_monthly=False, is_grib=False):
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing model data: {path}")
            
            datasets = []
            if is_grib:
                import cfgrib
                datasets = cfgrib.open_datasets(path)
            else:
                datasets = [xr.open_dataset(path)]
            
            tensors = []
            for v in var_names:
                tensor_found = None
                for ds in datasets:
                    if is_monthly:
                        time_dim = 'time' if 'time' in ds else 'valid_time' if 'valid_time' in ds else None
                        if time_dim:
                            ds = ds.sel({time_dim: slice(f"{date} 00:00:00", f"{date} 23:59:59")}).mean(dim=time_dim)
                            
                    ds_interp = ds.interp(latitude=self.target_lats, longitude=self.target_lons, method='nearest')
                    
                    matched = [key for key in ds_interp.data_vars if v.split('_')[0] in key.lower()]
                    if matched:
                        tensor_found = torch.tensor(ds_interp[matched[0]].values, dtype=torch.float32)
                        break
                
                if tensor_found is None:
                    # Fallback if variable is totally missing
                    logger.warning(f"Variable {v} missing in {path}, filling with zeros.")
                    tensor_found = torch.zeros(self.target_shape, dtype=torch.float32)
                tensors.append(tensor_found)
            
            for ds in datasets:
                ds.close()
            return tensors

        # GFS Variables (Rain, Temp, U, V)
        gfs_vars = load_strict(gfs_path, ['tp', 't2m', 'u10', 'v10'], is_grib=True)
        gfs_rain, gfs_temp, gfs_wind_u, gfs_wind_v = gfs_vars
        gfs_wind_mag = torch.sqrt(gfs_wind_u**2 + gfs_wind_v**2)
        gfs_rain = gfs_rain * 1000.0 # Convert meters to mm if needed

        # GraphCast Variables
        ai_vars = load_strict(ai_path, ['precipitation', 'temperature', 'u_component', 'v_component'], is_monthly=True)
        ai_rain, ai_temp, ai_wind_u, ai_wind_v = ai_vars
        ai_wind_mag = torch.sqrt(ai_wind_u**2 + ai_wind_v**2)
        ai_rain = ai_rain * 1000.0 # Convert meters to mm if needed

        # --- 3. Stack Inputs (Normalized) ---
        inputs = torch.stack([
            self._normalize(gfs_rain), self._normalize(gfs_temp), self._normalize(gfs_wind_mag),
            self._normalize(ai_rain), self._normalize(ai_temp), self._normalize(ai_wind_mag),
            self._normalize(dem)
        ], dim=0) # 7 Channels

        # Lead Time conditioning
        lead_time = torch.tensor([24.0], dtype=torch.float32)

        # Forecasts to Blend [Models, H, W]
        f_rain = torch.stack([gfs_rain, ai_rain], dim=0)
        f_temp = torch.stack([gfs_temp, ai_temp], dim=0)
        f_wind = torch.stack([gfs_wind_mag, ai_wind_mag], dim=0)
        
        # Targets
        t_rain = target_rain.unsqueeze(0)
        t_temp = target_temp.unsqueeze(0)
        t_wind = target_wind_mag.unsqueeze(0)

        return inputs, lead_time, (f_rain, f_temp, f_wind), (t_rain, t_temp, t_wind)
