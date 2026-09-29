import torch
import torch.nn as nn

class ContinuousExtremeWeightedMSELoss(nn.Module):
    def __init__(self, alpha=0.5, beta=2.0):
        """
        Continuous Power-Law Scaled MSE Loss.
        Provides smooth gradients while heavily penalizing errors on large target values.
        weight = 1.0 + alpha * (target ** beta)
        """
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.mse = nn.MSELoss(reduction='none')

    def forward(self, blended_pred, target):
        base_loss = self.mse(blended_pred, target)

        # Create a continuous weight multiplier.
        # Clamp at 0 to prevent issues with negative values (if any exist in data).
        weight_mask = 1.0 + self.alpha * torch.pow(torch.clamp(target, min=0.0), self.beta)

        # Apply mask and return the mean loss over the batch
        return torch.mean(base_loss * weight_mask)

if __name__ == '__main__':
    # Unit Test for the Loss Function
    loss_fn = ContinuousExtremeWeightedMSELoss(alpha=0.5, beta=2.0)

    # Batch size 1, 1 Channel, 2x2 Grid
    target = torch.tensor([[[[5.0, 25.0], [0.0, 10.0]]]])
    pred   = torch.tensor([[[[5.0, 15.0], [0.0, 10.0]]]])

    loss = loss_fn(pred, target)
    print(f"Calculated Loss: {loss.item()}")
