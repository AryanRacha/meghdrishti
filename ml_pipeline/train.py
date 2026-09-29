import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm
import logging
from models.unet_blender import SuperUNetBlender
from data_loaders.weather_dataset import ProductionWeatherDataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompositeLoss(nn.Module):
    def __init__(self, alpha=0.5, beta=2.0, rain_p90=8.0):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.rain_p90 = rain_p90 # Extreme rain threshold
        self.mse = nn.MSELoss()

    def forward(self, pred_rain, target_rain, pred_temp, target_temp, pred_wind, target_wind):
        # 1. Temperature & Wind Loss (Standard MSE)
        loss_temp = self.mse(pred_temp, target_temp)
        loss_wind = self.mse(pred_wind, target_wind)

        # 2. Extreme Weighted Rain Loss
        base_rain_loss = (pred_rain - target_rain) ** 2
        extreme_mask = (target_rain > self.rain_p90).float()
        penalty_weights = 1.0 + (extreme_mask * self.alpha * torch.exp(self.beta * (target_rain - self.rain_p90) / self.rain_p90))
        loss_rain = torch.mean(base_rain_loss * penalty_weights)

        # 3. Z-Score Scale Normalization (Approximate empirical weights to balance gradients)
        # Temp is usually ~300K, Rain is ~10mm, Wind is ~5m/s
        # Without this, Temp gradients will crush Rain gradients.
        total_loss = (loss_rain * 1.0) + (loss_temp * 0.01) + (loss_wind * 0.5)
        return total_loss, loss_rain, loss_temp, loss_wind

def train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Target execution device: {device}")
    
    if torch.cuda.is_available():
        logger.info(f"Detected GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB VRAM)")
        
    dates = [f"2023-08-{d:02d}" for d in range(1, 32)]
    
    # Initialize Dataset
    data_dir = os.path.join(os.path.dirname(__file__), 'data/processed')
    train_dataset = ProductionWeatherDataset(data_dir=data_dir, dates=dates)
    
    # BATCH SIZE REDUCED to 16 to prevent VRAM exhaustion with new Super-UNet
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=0)
    
    # Initialize Super-UNet
    # 7 input channels, 2 models (GFS & GraphCast)
    model = SuperUNetBlender(n_channels=7, n_models=2, features=[32, 64, 128, 256]).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    criterion = CompositeLoss(alpha=0.5, beta=2.0)
    
    epochs = 500
    patience = 15
    patience_counter = 0
    best_loss = float('inf')
    
    logger.info(f"Initialized pipeline -> Batch Size: 16, AMP: True")
    
    scaler = torch.amp.GradScaler('cuda')
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        for batch_idx, (inputs, lead_time, forecasts, targets) in enumerate(progress_bar):
            inputs = inputs.to(device)
            lead_time = lead_time.to(device)
            
            f_rain, f_temp, f_wind = [f.to(device) for f in forecasts]
            t_rain, t_temp, t_wind = [t.to(device) for t in targets]
            
            optimizer.zero_grad()
            
            with torch.amp.autocast('cuda'):
                # Forward Pass
                w_rain, w_temp, w_wind = model(inputs, lead_time)
                
                # Blend Forecasts
                blend_rain = torch.sum(w_rain * f_rain, dim=1, keepdim=True)
                blend_temp = torch.sum(w_temp * f_temp, dim=1, keepdim=True)
                blend_wind = torch.sum(w_wind * f_wind, dim=1, keepdim=True)
                
                # Compute Composite Loss
                loss, l_rain, l_temp, l_wind = criterion(blend_rain, t_rain, blend_temp, t_temp, blend_wind, t_wind)
                
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            total_loss += loss.item()
            progress_bar.set_postfix({'loss': f"{loss.item():.4f}", 'r_loss': f"{l_rain.item():.4f}"})
            
        avg_loss = total_loss / len(train_loader)
        logger.info(f"Epoch {epoch+1} completed. Average Loss: {avg_loss:.4f}")
        
        # --- Early Stopping Logic ---
        if avg_loss < best_loss:
            best_loss = avg_loss
            patience_counter = 0
            torch.save(model.state_dict(), 'super_unet_blender_weights.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}! Best Loss: {best_loss:.4f}")
                break

    # Baseline Evaluation Check
    logger.info("Computing Simple Average Baseline vs Super-UNet...")
    model.eval()
    with torch.no_grad():
        inputs, lead_time, forecasts, targets = next(iter(train_loader))
        inputs, lead_time = inputs.to(device), lead_time.to(device)
        f_rain, t_rain = forecasts[0].to(device), targets[0].to(device)
        
        # Simple Average
        simple_blend = torch.mean(f_rain, dim=1, keepdim=True)
        simple_loss = criterion.mse(simple_blend, t_rain).item()
        
        # Super-UNet
        w_rain, _, _ = model(inputs, lead_time)
        ai_blend = torch.sum(w_rain * f_rain, dim=1, keepdim=True)
        ai_loss = criterion.mse(ai_blend, t_rain).item()
        
        logger.info(f"Baseline MSE (Simple Avg): {simple_loss:.4f}")
        logger.info(f"Super-UNet MSE (AI Blend): {ai_loss:.4f}")
        if ai_loss < simple_loss:
            logger.info("✅ SUCCESS: AI dynamically outperformed the mathematical baseline!")
        else:
            logger.warning("❌ WARNING: AI failed to beat the simple average.")

    weights_path = "super_unet_blender_weights.pth"
    torch.save(model.state_dict(), weights_path)
    logger.info(f"Model saved successfully to {weights_path}")

if __name__ == '__main__':
    train()
