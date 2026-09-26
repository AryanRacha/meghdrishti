# 1 - Data Pipeline

## Objective
Automate the fetching and preprocessing of NWP forecasts and ground-truth meteorological data.

## Implemented Components
- **ml_pipeline/data_fetchers/gfs_fetcher.py**: Downloads historical GFS GRIB2 forecasts from NOAA's public AWS S3 bucket (
oaa-gfs-bdp-pds).
- **ml_pipeline/data_fetchers/era5_fetcher.py**: Fetches ERA5 reanalysis ground truth (precipitation) using the Copernicus cdsapi. Bounding box is restricted to India to save space.
- **ml_pipeline/utils/regrid.py**: Uses xarray to align longitude standards (0-360 vs -180/180) and interpolate resolutions between different models.

## Execution Commands
- **Fetch GFS**: python ml_pipeline/data_fetchers/gfs_fetcher.py
- **Fetch ERA5**: Requires user to place API key in ~/.cdsapirc. Then run python ml_pipeline/data_fetchers/era5_fetcher.py.
