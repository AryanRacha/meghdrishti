import os
import logging
from typing import Dict, List, Tuple
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm

from models.unet_blender import UNetBlender
from models.loss import ContinuousExtremeWeightedMSELoss
from data_loaders.weather_dataset import ProductionWeatherDataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train() -> None:
    # Hardware verification and setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    use_cuda = device.type == 'cuda'
    
    logger.info(f"Target execution device: {device}")
    if use_cuda:
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        logger.info(f"Detected GPU: {gpu_name} ({vram_gb:.2f} GB VRAM)")
    else:
        logger.info("CUDA device not detected; executing fallback on CPU.")

    # High-performance hyperparameters optimized for 24GB RTX 4090
    BATCH_SIZE: int = 32  # Scaled up for 24GB VRAM footprint (can scale to 64 if memory headroom permits)
    LEARNING_RATE: float = 1e-4
    EPOCHS: int = 5
    ACCUMULATION_STEPS: int = 1  # Deactivated (step per batch) for direct high-throughput parallel execution

    # Dataloader configurations
    stats_dict: Dict[str, Tuple[float, float]] = {
        'gfs': (5.0, 10.0),
        'ai': (4.5, 9.5),
        'dem': (500.0, 1000.0),
        'lead_time': (24.0, 1.0)
    }
    dates: List[str] = ['2023-08-01', '2023-08-02']

    data_dir = os.path.join(os.path.dirname(__file__), '../data/processed')
    train_dataset = ProductionWeatherDataset(
        data_dir=data_dir,
        dates=dates,
        stats_dict=stats_dict,
        target_shape=(128, 128)
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4 if use_cuda else 0,
        pin_memory=use_cuda
    )

    # Spatial U-Net Model (4 input channels: GFS, AI, DEM, Lead Time; 2 output weight channels)
    model = UNetBlender(n_channels=4, n_models=2, features=[32, 64, 128, 256]).to(device)

    # Optimizer, Extreme Weather Preserving Loss, and AMP Scaler
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    criterion = ContinuousExtremeWeightedMSELoss(alpha=0.5, beta=2.0)
    scaler = torch.amp.GradScaler('cuda', enabled=use_cuda)

    logger.info(
        f"Initialized pipeline -> Batch Size: {BATCH_SIZE}, "
        f"Accumulation Steps: {ACCUMULATION_STEPS}, AMP: {use_cuda}"
    )

    # Training Loop
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0.0

        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}")
        optimizer.zero_grad()

        for batch_idx, (inputs, forecasts, targets) in enumerate(progress_bar):
            inputs = inputs.to(device, non_blocking=use_cuda)
            forecasts = forecasts.to(device, non_blocking=use_cuda)
            targets = targets.to(device, non_blocking=use_cuda)

            # Mixed Precision Forward Pass (Tensor Cores)
            with torch.amp.autocast('cuda', enabled=use_cuda):
                # 1. Forward Pass: Predict spatial blending weight maps
                weight_maps = model(inputs)  # Shape: [Batch, 2, H, W]

                # 2. Compute Blended Forecast
                blended_prediction = torch.sum(weight_maps * forecasts, dim=1, keepdim=True)  # Shape: [Batch, 1, H, W]

                # 3. Calculate Loss with Extreme Weather Weighting
                loss = criterion(blended_prediction, targets)
                loss = loss / ACCUMULATION_STEPS

            # 4. Backward Pass & Scaled Step
            scaler.scale(loss).backward()

            if (batch_idx + 1) % ACCUMULATION_STEPS == 0 or (batch_idx + 1) == len(train_loader):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()

            loss_val = loss.item() * ACCUMULATION_STEPS
            epoch_loss += loss_val
            progress_bar.set_postfix({'loss': f"{loss_val:.4f}"})

        avg_loss = epoch_loss / len(train_loader) if len(train_loader) > 0 else 0.0
        logger.info(f"Epoch {epoch+1} completed. Average Loss: {avg_loss:.4f}")

    weights_path = "unet_blender_weights.pth"
    logger.info(f"Training complete. Saving weights to {weights_path}...")
    torch.save(model.state_dict(), weights_path)
    logger.info(f"Model saved successfully to {weights_path}")

if __name__ == '__main__':
    train()
