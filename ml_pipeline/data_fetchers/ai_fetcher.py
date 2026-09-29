import os
import xarray as xr
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_synthetic_graphcast(date="2023-08", input_era5_dir="data/raw/era5", output_dir="data/raw/ai"):
    """
    Generates a synthetic AI forecast (GraphCast proxy) by taking the ERA5 ground truth
    and applying mathematical gaussian noise/blur. This is a standard hackathon tactic 
    to prove a blending architecture works when real AI historic inference isn't available.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    year, month = date.split('-')
    era5_path = os.path.join(input_era5_dir, f"era5_{year}_{month}.nc")
    output_path = os.path.join(output_dir, f"graphcast_{year}_{month}.nc")
    
    if not os.path.exists(era5_path):
        logger.error(f"ERA5 ground truth missing: {era5_path}. Run download_production_data.py first.")
        return

    logger.info(f"Generating Synthetic GraphCast Forecasts for {date} based on ERA5 ground truth...")
    
    # Open ERA5 ground truth
    ds = xr.open_dataset(era5_path)
    
    # We will rename the variables to match the GraphCast format expected by weather_dataset.py
    # ERA5: 'tp', 't2m', 'u10', 'v10'
    # GraphCast: 'precipitation', 'temperature', 'u_component', 'v_component'
    
    ds_synthetic = xr.Dataset(
        coords=ds.coords,
        attrs={"description": "Synthetic GraphCast Forecast for SIH Prototype"}
    )
    
    # Add noise to simulate an AI forecast that isn't perfectly accurate
    np.random.seed(42)
    
    logger.info("Applying noise patterns to Rain, Temp, and Wind...")
    
    # Precipitation (AI models often underestimate extremes, so we apply a slight reduction + noise)
    if 'tp' in ds:
        noise_rain = np.random.normal(0, 0.002, ds['tp'].shape)
        ds_synthetic['precipitation'] = (ds['tp'] * 0.9) + noise_rain
    else:
        # Fallback if ERA5 download missed 'tp' due to CDS API limits
        logger.warning("'tp' missing from ERA5, generating fully synthetic precipitation...")
        ds_synthetic['precipitation'] = (xr.DataArray(np.random.exponential(0.005, ds['t2m'].shape), coords=ds['t2m'].coords))
        
    ds_synthetic['precipitation'] = ds_synthetic['precipitation'].clip(min=0)
    
    # Temperature (AI models are usually very good here, slight noise)
    noise_temp = np.random.normal(0, 1.5, ds['t2m'].shape) # 1.5 Kelvin noise
    ds_synthetic['temperature'] = ds['t2m'] + noise_temp
    
    # Wind
    noise_u = np.random.normal(0, 2.0, ds['u10'].shape)
    noise_v = np.random.normal(0, 2.0, ds['v10'].shape)
    ds_synthetic['u_component'] = ds['u10'] + noise_u
    ds_synthetic['v_component'] = ds['v10'] + noise_v
    
    logger.info(f"Saving synthetic AI forecast to {output_path}...")
    ds_synthetic.to_netcdf(output_path)
    ds.close()
    
    logger.info("✅ Synthetic GraphCast generation complete! The Super-UNet can now train.")

if __name__ == "__main__":
    generate_synthetic_graphcast()
