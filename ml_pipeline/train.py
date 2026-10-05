import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
from tqdm import tqdm
import logging
import math
from models.unet_blender import SuperUNetBlender
from data_loaders.weather_dataset import ProductionWeatherDataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MaskedExtremeLoss(nn.Module):
    def __init__(self, alpha=0.5, beta=2.0, rain_threshold=64.5, temp_threshold=42.0, wind_threshold=33.0):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.rain_threshold = rain_threshold
        self.temp_threshold = temp_threshold
        self.wind_threshold = wind_threshold
        self.mse = nn.MSELoss(reduction='none')

    def forward_rain(self, pred, target):
        # Masked Loss: Only penalize where target or pred indicates rain (>0.1mm)
        # This prevents dry winter days from numbing the network
        rain_mask = (target > 0.1) | (pred > 0.1)
        if not rain_mask.any():
            return torch.tensor(0.0, device=pred.device, requires_grad=True)
            
        base_loss = self.mse(pred, target)
        extreme_mask = (target > self.rain_threshold).float()
        penalty = 1.0 + (extreme_mask * self.alpha * torch.exp(self.beta * (target - self.rain_threshold) / self.rain_threshold))
        
        return torch.mean(base_loss[rain_mask] * penalty[rain_mask])

    def forward_temp(self, pred, target):
        base_loss = self.mse(pred, target)
        extreme_mask = (target > self.temp_threshold).float()
        penalty = 1.0 + (extreme_mask * self.alpha * torch.exp(self.beta * (target - self.temp_threshold) / self.temp_threshold))
        return torch.mean(base_loss * penalty)

    def forward_wind(self, pred_u, pred_v, target_u, target_v):
        pred_mag = torch.sqrt(pred_u**2 + pred_v**2 + 1e-8)
        target_mag = torch.sqrt(target_u**2 + target_v**2 + 1e-8)
        
        base_loss = self.mse(pred_u, target_u) + self.mse(pred_v, target_v)
        extreme_mask = (target_mag > self.wind_threshold).float()
        penalty = 1.0 + (extreme_mask * self.alpha * torch.exp(self.beta * (target_mag - self.wind_threshold) / self.wind_threshold))
        
        return torch.mean(base_loss * penalty)

def train_loso_fold(fold_name, train_dates, val_dates, data_dir, device):
    logger.info(f"--- Starting {fold_name} ---")
    
    train_dataset = ProductionWeatherDataset(data_dir=data_dir, dates=train_dates)
    val_dataset = ProductionWeatherDataset(data_dir=data_dir, dates=val_dates)
    
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, num_workers=4, pin_memory=True)
    
    model = SuperUNetBlender(n_channels=13, n_models=2, features=[32, 64, 128, 256]).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    criterion = MaskedExtremeLoss()
    scaler = torch.amp.GradScaler('cuda')
    
    epochs = 200
    patience = 15
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        for inputs, condition, forecasts, targets in progress_bar:
            inputs, condition = inputs.to(device), condition.to(device)
            f_rain, f_temp, f_u, f_v = [f.to(device) for f in forecasts]
            t_rain, t_temp, t_u, t_v = [t.to(device) for t in targets]
            
            optimizer.zero_grad(set_to_none=True)
            
            with torch.amp.autocast('cuda'):
                heads = model(inputs, condition)
                (w_rain, res_rain), (w_temp, res_temp), (w_u, res_u), (w_v, res_v) = heads
                
                # Blend (Softmax weights * inputs) + Residual Bias
                pred_rain = torch.sum(w_rain * f_rain, dim=1, keepdim=True) + res_rain
                pred_temp = torch.sum(w_temp * f_temp, dim=1, keepdim=True) + res_temp
                pred_u = torch.sum(w_u * f_u, dim=1, keepdim=True) + res_u
                pred_v = torch.sum(w_v * f_v, dim=1, keepdim=True) + res_v
                
                # Compute independent losses
                l_rain = criterion.forward_rain(pred_rain, t_rain)
                l_temp = criterion.forward_temp(pred_temp, t_temp)
                l_wind = criterion.forward_wind(pred_u, pred_v, t_u, t_v)
                
            # Elite PyTorch Trick: Sequential independent backward passes in FP16 
            # to prevent gradient underflow when dealing with multi-scale targets
            if l_rain.requires_grad:
                scaler.scale(l_rain).backward(retain_graph=True)
            scaler.scale(l_temp).backward(retain_graph=True)
            scaler.scale(l_wind).backward()
            
            # Gradient clipping to stabilize the residual heads
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            scaler.step(optimizer)
            scaler.update()
            
            batch_total = l_rain.item() + l_temp.item() + l_wind.item()
            total_loss += batch_total
            progress_bar.set_postfix({'loss': f"{batch_total:.4f}"})
            
        # Validation Phase
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for inputs, condition, forecasts, targets in val_loader:
                inputs, condition = inputs.to(device), condition.to(device)
                f_rain, f_temp, f_u, f_v = [f.to(device) for f in forecasts]
                t_rain, t_temp, t_u, t_v = [t.to(device) for t in targets]
                
                with torch.amp.autocast('cuda'):
                    heads = model(inputs, condition)
                    (w_rain, res_rain), (w_temp, res_temp), (w_u, res_u), (w_v, res_v) = heads
                    pred_rain = torch.sum(w_rain * f_rain, dim=1, keepdim=True) + res_rain
                    pred_temp = torch.sum(w_temp * f_temp, dim=1, keepdim=True) + res_temp
                    pred_u = torch.sum(w_u * f_u, dim=1, keepdim=True) + res_u
                    pred_v = torch.sum(w_v * f_v, dim=1, keepdim=True) + res_v
                    
                    val_loss += criterion.forward_rain(pred_rain, t_rain).item()
                    val_loss += criterion.forward_temp(pred_temp, t_temp).item()
                    val_loss += criterion.forward_wind(pred_u, pred_v, t_u, t_v).item()
                    
        val_loss /= len(val_loader)
        logger.info(f"Epoch {epoch+1} | Train Loss: {total_loss/len(train_loader):.4f} | Val Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), f'super_unet_v2_{fold_name}.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch+1}! Best Val Loss: {best_val_loss:.4f}")
                break

def train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Target execution device: {device}")
    
    # 3-Fold Leave-One-Season-Out (LOSO) Split
    # Hold out 2023 entirely for production testing.
    dates_2020 = [f"2020-08-{d:02d}" for d in range(1, 32)] # Mock placeholder for actual datasets
    dates_2021 = [f"2021-08-{d:02d}" for d in range(1, 32)]
    dates_2022 = [f"2022-08-{d:02d}" for d in range(1, 32)]
    
    data_dir = os.path.join(os.path.dirname(__file__), 'data/processed')
    
    # Fold 1: Train 21, 22 -> Val 20
    train_loso_fold("Fold_1", dates_2021 + dates_2022, dates_2020, data_dir, device)
    
    # In practice, you would run the other folds and average the checkpoints.
    # train_loso_fold("Fold_2", dates_2020 + dates_2022, dates_2021, data_dir, device)
    # train_loso_fold("Fold_3", dates_2020 + dates_2021, dates_2022, data_dir, device)

if __name__ == '__main__':
    train()
