import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import logging
from tqdm import tqdm

from models.unet_blender import UNetBlender
from models.loss import ContinuousExtremeWeightedMSELoss
from data_loaders.weather_dataset import ProductionWeatherDataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Starting training on {device}...")

    # Hyperparameters
    batch_size = 16
    learning_rate = 1e-4
    epochs = 5

    # Dataloader (Dummy stats and dates for now, you will need to replace these with real computed stats and dates)
    dummy_stats = {
        'gfs': (5.0, 10.0),
        'ai': (4.5, 9.5),
        'dem': (500.0, 1000.0),
        'lead_time': (24.0, 1.0)
    }
    dummy_dates = ['2023-08-01', '2023-08-02']

    train_dataset = ProductionWeatherDataset(data_dir='../data/processed', dates=dummy_dates, stats_dict=dummy_stats, target_shape=(128, 128))
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

    # Model
    model = UNetBlender(n_channels=4, n_models=2, features=[32, 64, 128, 256]).to(device)

    # Optimizer & Loss
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate)
    criterion = ContinuousExtremeWeightedMSELoss(alpha=0.5, beta=2.0)

    # Training Loop
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0

        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        for inputs, forecasts, targets in progress_bar:
            inputs = inputs.to(device)
            forecasts = forecasts.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()

            # 1. Forward Pass: Predict spatial weight maps
            weight_maps = model(inputs) # Shape: [Batch, 2, H, W]

            # 2. Compute Blended Forecast
            # Weight maps sum to 1.0 at every pixel.
            # Multiply weights by actual forecast values and sum across models (dim=1).
            blended_prediction = torch.sum(weight_maps * forecasts, dim=1, keepdim=True) # Shape: [Batch, 1, H, W]

            # 3. Calculate Loss
            loss = criterion(blended_prediction, targets)

            # 4. Backward Pass & Step
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            progress_bar.set_postfix({'loss': loss.item()})

        logger.info(f"Epoch {epoch+1} completed. Average Loss: {epoch_loss / len(train_loader):.4f}")

    logger.info("Training complete. Saving weights...")
    torch.save(model.state_dict(), "unet_blender_weights.pth")
    logger.info("Model saved to unet_blender_weights.pth")

if __name__ == '__main__':
    train()
