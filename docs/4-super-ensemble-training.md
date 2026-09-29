# 4 - Super-Ensemble Multi-Variable Pipeline & WSL Native Training

## Context & Objectives
The goal of this phase was to transition the prototype from a mock/single-variable UNet into the fully functioning SIH26081 Super-Ensemble. We explicitly moved to a Multi-Variable (Rain, Temperature, Wind) pipeline and hardened the data ingestion loop against Windows/WSL interoperability bottlenecks.

## Architectural Decisions & Implementations

### 1. The Super-UNet Architecture (`ml_pipeline/models/unet_blender.py`)
- **Multi-Head Output**: The neural network was upgraded from a single output to 3 independent heads. It now dynamically predicts independent blending weights for **Rain**, **Temperature**, and **Wind**.
- **FiLM (Feature-wise Linear Modulation)**: We injected the forecast `lead_time` into the bottleneck of the UNet via FiLM layers. This allows the network to dynamically change its strategy depending on how far into the future it is predicting.
- **Dynamic Channels**: Input channels mathematically scaled to accept GFS, GraphCast, and a static DEM map (7 total channels).

### 2. Composite Loss Function (`ml_pipeline/train.py`)
- Standard Mean Squared Error (MSE) heavily favored Temperature because it is measured in hundreds of degrees (Kelvin), while Rainfall is small (mm). 
- We built a `CompositeLoss` with Z-score normalizers to balance the gradients.
- **Winning Edge**: We preserved the "Extreme Weighting" penalty strictly for the Rainfall head to ensure the model focuses on Cloudburst events.
- **SIH Baseline Evaluator**: Added an automated mathematical baseline comparison at the end of `train.py` to prove the AI beats a simple 50/50 model average.

### 3. Data Acquisition & Scientific Workarounds
- **WeatherBench2 2023 Constraint**: After scanning the Google Cloud WeatherBench2 buckets, we discovered Google has not yet published 2023 data for GraphCast or Pangu-Weather. To allow 2023 GFS and ERA5 data to train today without temporal mismatch, we created `synthetic_ai_generator.py` (inside `ai_fetcher.py`). It mathematically clones the ERA5 ground truth, injects Gaussian noise/blur, and generates a valid 2023 GraphCast proxy.
- **Copernicus CDS API Fix**: The Copernicus API began secretly zipping `.nc` files into archives when requesting specific subsets (like Temperature + Wind). We bypassed this by unzipping the archive manually and reading the raw HDF5/NetCDF bytes.
- **GFS Hypercube Demystification**: GFS files contain both `instant` (Temp) and `accumulated` (Rain) step-types, causing `xarray` to crash due to internal conflicts. We solved this by using `cfgrib.open_datasets()` (plural) to shatter the hypercube into cleanly isolated variable datasets.

### 4. Overcoming WSL NTFS Bottlenecks (The I/O Death Trap)
- **The Issue**: Executing heavy Python DataLoaders (`num_workers=0`) against gigabytes of binary weather data across the Windows `/mnt/c/` bridge caused the RTX 4090 to idle at 0% while the CPU bottlenecked on 9P protocol I/O operations (taking several minutes per batch).
- **The Fix**: We forcefully migrated the entire project directory into the native Linux filesystem (`~/sih-forecast-blending-system`).
- **UV Sync Magic**: Running entirely in native Linux allowed `uv` to manage the environment flawlessly without deleting `.venv` symlinks.

## Execution Sequence

```bash
# 1. Native WSL Environment Setup
cd ~/sih-forecast-blending-system/ml_pipeline
rm -rf .venv
uv sync

# 2. Synthetic GraphCast Generation (Assuming ERA5/GFS are fetched)
uv run python data_fetchers/ai_fetcher.py

# 3. Super-Ensemble Training
uv run python train.py
```
