import xarray as xr
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def align_longitude(ds):
    """
    Converts a dataset's longitude from [0, 360] to [-180, 180].
    GFS typically uses 0-360, while ERA5 uses -180 to 180 or vice versa.
    """
    if 'longitude' in ds.coords:
        lon_name = 'longitude'
    elif 'lon' in ds.coords:
        lon_name = 'lon'
    else:
        logger.warning("No longitude coordinate found.")
        return ds
        
    ds['_longitude_adjusted'] = xr.where(
        ds[lon_name] > 180,
        ds[lon_name] - 360,
        ds[lon_name]
    )
    ds = (
        ds
        .swap_dims({lon_name: '_longitude_adjusted'})
        .sel(**{'_longitude_adjusted': sorted(ds._longitude_adjusted)})
        .drop(lon_name)
    )
    ds = ds.rename({'_longitude_adjusted': lon_name})
    return ds

def regrid_to_target(source_ds, target_ds, method='bilinear'):
    """
    Regrids source_ds to the exact spatial coordinates of target_ds.
    Usually requires `xemsf` or `scipy` as an interpolator.
    Here we use xarray's built-in interp.
    """
    logger.info("Starting regridding process...")
    
    # Ensure longitude conventions match
    source_ds = align_longitude(source_ds)
    target_ds = align_longitude(target_ds)
    
    lon_name = 'longitude' if 'longitude' in target_ds.coords else 'lon'
    lat_name = 'latitude' if 'latitude' in target_ds.coords else 'lat'
    
    logger.info(f"Interpolating source data to target grid using {method} method.")
    
    # Simple interpolation (suitable for MVP). For production, use xesmf for conservative regridding.
    regridded_ds = source_ds.interp(
        {
            lat_name: target_ds[lat_name],
            lon_name: target_ds[lon_name]
        },
        method=method,
        kwargs={"fill_value": "extrapolate"}
    )
    
    logger.info("Regridding complete.")
    return regridded_ds

if __name__ == "__main__":
    logger.info("Regrid utility functions ready.")
