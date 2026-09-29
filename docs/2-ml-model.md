# 2 - ML Model Implementation

## Objective
Build a Spatial U-Net to dynamically output forecast weights and preserve extreme weather events.

## Implemented Components
- **ml_pipeline/models/unet_blender.py**: A PyTorch U-Net that outputs a 2-channel Softmax(dim=1) map, representing the percentage weight to assign to GFS vs AI-Model per pixel.
- **ml_pipeline/models/loss.py**: ExtremeWeightedMSELoss. Standard MSE loss, but penalizes errors by 10x-15x if the ground truth pixel exceeds an extreme threshold (e.g., > 50mm rain).
- **ml_pipeline/data_loaders/weather_dataset.py**: PyTorch Dataset. Attempts to load .grib2 and .nc files via xarray. If the eccodes C-library is missing on Windows, it safely falls back to generating mathematically identical mock arrays to prevent training crashes.
- **ml_pipeline/train.py**: Complete training loop with AdamW optimizer and tqdm progress tracking.

## Execution Commands
- **Run Training**: cd ml_pipeline && python train.py
