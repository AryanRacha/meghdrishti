import os
import torch
import numpy as np
from torch.utils.data import DataLoader
from models.unet_blender import SuperUNetBlender
from data_loaders.weather_dataset import ProductionWeatherDataset
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def evaluate():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Evaluation device: {device}")
    
    dates = [f"2023-09-{d:02d}" for d in range(1, 31)]
    
    data_dir = os.path.join(os.path.dirname(__file__), 'data/processed')
    eval_dataset = ProductionWeatherDataset(
        data_dir=data_dir,
        dates=dates,
        target_shape=(128, 128)
    )
    
    eval_loader = DataLoader(
        eval_dataset,
        batch_size=30,
        shuffle=False,
        num_workers=0
    )
    
    model = SuperUNetBlender(n_channels=7, n_models=2, features=[32, 64, 128, 256]).to(device)
    
    weights_path = "super_unet_blender_weights.pth"
    if not os.path.exists(weights_path):
        logger.error(f"Weights file {weights_path} not found!")
        return
        
    model.load_state_dict(torch.load(weights_path, map_location=device, weights_only=True))
    model.eval()
    logger.info("Model weights loaded successfully.")
    
    with torch.no_grad():
        for inputs, lead_time, forecasts, targets in eval_loader:
            inputs = inputs.to(device)
            lead_time = lead_time.to(device)
            
            f_rain, f_temp, f_wind = [f.to(device) for f in forecasts]
            t_rain, t_temp, t_wind = [t.to(device) for t in targets]
            
            w_rain, w_temp, w_wind = model(inputs, lead_time)  
            
            blend_rain = torch.sum(w_rain * f_rain, dim=1, keepdim=True)
            
            # Standard Metrics for Rain
            mse = torch.mean((blend_rain - t_rain) ** 2).item()
            mae = torch.mean(torch.abs(blend_rain - t_rain)).item()
            
            # Threshold for POD/FAR/CSI (Extreme Rain > 8.0)
            threshold = 8.0
            pred_event = (blend_rain > threshold)
            true_event = (t_rain > threshold)
            
            hits = torch.sum(pred_event & true_event).item()
            false_alarms = torch.sum(pred_event & ~true_event).item()
            misses = torch.sum(~pred_event & true_event).item()
            
            pod = hits / (hits + misses) if (hits + misses) > 0 else 0.0
            far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else 0.0
            csi = hits / (hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else 0.0
            
            logger.info(f"--- Evaluation Metrics (September 2023) ---")
            logger.info(f"Blended Rain RMSE: {np.sqrt(mse):.4f}")
            logger.info(f"Blended Rain MAE:  {mae:.4f}")
            logger.info(f"--- Extreme Rain (>{threshold}mm) ---")
            logger.info(f"Probability of Detection (POD): {pod:.4f}")
            logger.info(f"False Alarm Ratio (FAR):        {far:.4f}")
            logger.info(f"Critical Success Index (CSI):   {csi:.4f}")
            logger.info(f"-------------------------------------------")

if __name__ == '__main__':
    evaluate()
