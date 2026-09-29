import os
import torch
import numpy as np
from torch.utils.data import DataLoader
from models.unet_blender import UNetBlender
from data_loaders.weather_dataset import ProductionWeatherDataset
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def evaluate():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Evaluation device: {device}")
    
    # We trained on August 2023. Let's evaluate on September 2023 (unseen data).
    dates = [f"2023-09-{d:02d}" for d in range(1, 31)]
    
    stats_dict = {
        'gfs': (5.0, 10.0),
        'ai': (4.5, 9.5),
        'dem': (500.0, 1000.0),
        'lead_time': (24.0, 1.0)
    }
    
    data_dir = os.path.join(os.path.dirname(__file__), 'data/processed')
    eval_dataset = ProductionWeatherDataset(
        data_dir=data_dir,
        dates=dates,
        stats_dict=stats_dict,
        target_shape=(128, 128)
    )
    
    eval_loader = DataLoader(
        eval_dataset,
        batch_size=30,  # All 30 days of Sept in one batch for fast evaluation
        shuffle=False,
        num_workers=0
    )
    
    model = UNetBlender(n_channels=4, n_models=2, features=[32, 64, 128, 256]).to(device)
    
    weights_path = "unet_blender_weights.pth"
    if not os.path.exists(weights_path):
        logger.error(f"Weights file {weights_path} not found!")
        return
        
    model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
    model.eval()
    logger.info("Model weights loaded successfully.")
    
    with torch.no_grad():
        for inputs, forecasts, targets in eval_loader:
            inputs = inputs.to(device)
            forecasts = forecasts.to(device)
            targets = targets.to(device)
            
            # Predict spatial blending weight maps
            weight_maps = model(inputs)  
            
            # Compute Blended Forecast
            blended_prediction = torch.sum(weight_maps * forecasts, dim=1, keepdim=True)
            
            # Standard Metrics
            mse = torch.mean((blended_prediction - targets) ** 2).item()
            mae = torch.mean(torch.abs(blended_prediction - targets)).item()
            
            # Compare with raw GFS (which is channel 0 of the forecasts)
            gfs_only = forecasts[:, 0:1, :, :] 
            gfs_mse = torch.mean((gfs_only - targets) ** 2).item()
            gfs_mae = torch.mean(torch.abs(gfs_only - targets)).item()
            
            logger.info(f"--- Evaluation Metrics (September 2023) ---")
            logger.info(f"Blended Model MSE: {mse:.4f}")
            logger.info(f"Raw GFS MSE:       {gfs_mse:.4f}")
            logger.info(f"---")
            logger.info(f"Blended Model MAE: {mae:.4f}")
            logger.info(f"Raw GFS MAE:       {gfs_mae:.4f}")
            logger.info(f"-------------------------------------------")
            
            if mse < gfs_mse:
                logger.info("✅ SUCCESS: AI Blended model outperformed raw GFS!")
            else:
                logger.warning("❌ Blended model underperformed compared to GFS.")
            
if __name__ == '__main__':
    evaluate()
