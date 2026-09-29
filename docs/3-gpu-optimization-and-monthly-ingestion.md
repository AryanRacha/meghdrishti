# 3 - GPU Optimization & Monthly Data Ingestion Pipeline

## Objective
Accelerate data ingestion and training throughput to leverage enterprise-grade GPU hardware (NVIDIA RTX 4090, 24GB VRAM).

## Implemented Components

### 1. Monthly Chunk Ingestion (`ml_pipeline/download_production_data.py`)
- **Batched Retrieval**: Replaced daily request iterations with single-request monthly day arrays (`day: [01..30/31]`).
- **Target Monsoon Scope**: Configured for June, July, August, and September across 2021, 2022, and 2023.
- **Connection Robustness**: Set CDS client timeout to 600s (`cdsapi.Client(timeout=600)`) to eliminate object-store read timeouts.
- **Storage Standard**: Standardized output naming to `data/raw/era5/era5_{year}_{month}.nc`.

### 2. High-Throughput GPU Training Configuration (`ml_pipeline/train.py`)
- **Memory Footprint Scaling**: Increased `BATCH_SIZE` to 32 (expandable to 64 for 24GB VRAM).
- **Gradient Accumulation Deactivation**: Set `ACCUMULATION_STEPS = 1` for immediate parallelized backpropagation across the RTX 4090 architecture.
- **Automatic Mixed Precision (AMP)**: Integrated `torch.amp.autocast('cuda')` and `torch.amp.GradScaler('cuda')` to utilize 4th-Gen Tensor Cores.
- **I/O Acceleration**: Configured `DataLoader` with `num_workers=4` and `pin_memory=True` on CUDA devices.
- **Extreme Event Loss**: Preserved continuous extreme-weighted MSE loss to protect high-impact rainfall events.

## Execution & Verification Commands

### 1. Environment Sync
```bash
# In backend/
uv sync

# In ml_pipeline/
uv sync
```

### 2. RTX 4090 GPU Audit
```bash
cd ml_pipeline
uv run python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Device name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'); print('VRAM (GB):', torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0)"
```

### 3. Accelerated Production Data Download
```bash
cd ml_pipeline
uv run python download_production_data.py
```

### 4. GPU Training Execution
```bash
cd ml_pipeline
uv run python train.py
```
