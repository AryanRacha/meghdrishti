import os
import torch
import xarray as xr
import numpy as np
import cfgrib
from tqdm import tqdm

def preprocess_all():
    target_lats = np.linspace(38.0, 8.0, 128)
    target_lons = np.linspace(68.0, 98.0, 128)
    dates = [f"2023-08-{d:02d}" for d in range(1, 32)]
    
    os.makedirs('data/processed', exist_ok=True)
    
    print("Loading Monthly ERA5 and AI...")
    ds_era5 = xr.open_dataset('data/raw/era5/era5_2023_08.nc')
    if 'z' in ds_era5:
        dem_ds = ds_era5['z'].sel(valid_time=slice("2023-08-01", "2023-08-01 23:59:59")).mean(dim='valid_time')
        dem = torch.tensor(dem_ds.interp(latitude=target_lats, longitude=target_lons, method='nearest').values, dtype=torch.float32) / 9.80665
    else:
        dem = torch.zeros((128, 128), dtype=torch.float32)
    
    datasets_ai = [xr.open_dataset('data/raw/ai/graphcast_2023_08.nc')]
    
    for date in tqdm(dates, desc="Preprocessing Days"):
        # Load GFS
        gfs_path = f'data/raw/gfs/gfs_{date.replace("-", "")}_00z_f024.grib2'
        datasets_gfs = cfgrib.open_datasets(gfs_path)
        
        gfs_tensors = {}
        for ds in datasets_gfs:
            ds_interp = ds.interp(latitude=target_lats, longitude=target_lons, method='nearest')
            for v in ['tp', 't2m', 'u10', 'v10']:
                matched = [key for key in ds_interp.data_vars if v in key.lower()]
                if matched:
                    gfs_tensors[v] = torch.tensor(ds_interp[matched[0]].values, dtype=torch.float32)
        
        gfs_rain = gfs_tensors.get('tp', torch.zeros((128,128)))
        gfs_temp = gfs_tensors.get('t2m', torch.zeros((128,128)))
        gfs_wind = torch.sqrt(gfs_tensors.get('u10', torch.zeros((128,128)))**2 + gfs_tensors.get('v10', torch.zeros((128,128)))**2)
        
        # Load AI
        ai_tensors = {}
        for ds in datasets_ai:
            time_dim = 'time' if 'time' in ds else 'valid_time'
            ds_day = ds.sel({time_dim: slice(f"{date} 00:00:00", f"{date} 23:59:59")}).mean(dim=time_dim)
            ds_interp = ds_day.interp(latitude=target_lats, longitude=target_lons, method='nearest')
            for v in ['precipitation', 'temperature', 'u_component', 'v_component']:
                if v in ds_interp:
                    ai_tensors[v] = torch.tensor(ds_interp[v].values, dtype=torch.float32)
                    
        ai_rain = ai_tensors.get('precipitation', torch.zeros((128,128))) * 1000.0
        ai_temp = ai_tensors.get('temperature', torch.zeros((128,128)))
        ai_wind = torch.sqrt(ai_tensors.get('u_component', torch.zeros((128,128)))**2 + ai_tensors.get('v_component', torch.zeros((128,128)))**2)
        
        # Load Target
        day_era5 = ds_era5.sel(valid_time=slice(f"{date} 00:00:00", f"{date} 23:59:59")).mean(dim='valid_time')
        day_era5_interp = day_era5.interp(latitude=target_lats, longitude=target_lons, method='nearest')
        
        t_rain = torch.tensor(day_era5_interp['tp'].values, dtype=torch.float32) * 1000.0 if 'tp' in day_era5_interp else torch.zeros((128,128))
        t_temp = torch.tensor(day_era5_interp['t2m'].values, dtype=torch.float32)
        t_wind = torch.sqrt(torch.tensor(day_era5_interp['u10'].values)**2 + torch.tensor(day_era5_interp['v10'].values)**2)
        
        torch.save({
            'gfs': (gfs_rain, gfs_temp, gfs_wind),
            'ai': (ai_rain, ai_temp, ai_wind),
            'target': (t_rain, t_temp, t_wind),
            'dem': dem
        }, f'data/processed/{date}.pt')

if __name__ == "__main__":
    preprocess_all()
