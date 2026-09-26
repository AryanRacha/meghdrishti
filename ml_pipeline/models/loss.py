import torch
import torch.nn as nn

class ExtremeWeightedMSELoss(nn.Module):
    def __init__(self, extreme_threshold=50.0, penalty_weight=10.0):
        """
        Custom MSE Loss that heavily penalizes errors when the ground truth 
        is above a certain threshold (e.g., extreme rainfall events).
        
        Args:
            extreme_threshold (float): The value above which precipitation is considered extreme.
                                       This could be set based on the 90th/95th percentile of the dataset.
            penalty_weight (float): The multiplier applied to the loss for pixels exceeding the threshold.
        """
        super().__init__()
        self.threshold = extreme_threshold
        self.penalty = penalty_weight
        self.mse = nn.MSELoss(reduction='none')

    def forward(self, blended_pred, target):
        # Calculate standard pixel-wise MSE
        base_loss = self.mse(blended_pred, target)
        
        # Create a multiplier mask: 1.0 for normal rain, penalty for extreme rain
        weight_mask = torch.where(target >= self.threshold, self.penalty, 1.0)
        
        # Apply mask and return the mean loss over the batch
        return torch.mean(base_loss * weight_mask)

if __name__ == '__main__':
    # Unit Test for the Loss Function
    loss_fn = ExtremeWeightedMSELoss(extreme_threshold=20.0, penalty_weight=10.0)
    
    # Batch size 1, 1 Channel, 2x2 Grid
    target = torch.tensor([[[[5.0, 25.0], [0.0, 10.0]]]])
    pred   = torch.tensor([[[[5.0, 15.0], [0.0, 10.0]]]]) # Missed the 25.0 extreme event by 10.
    
    # Expected:
    # Error for 25.0 pixel = (25-15)^2 = 100 * penalty(10) = 1000
    # Error for other pixels = 0
    # Mean loss = 1000 / 4 = 250
    loss = loss_fn(pred, target)
    print(f"Calculated Loss: {loss.item()} (Expected: 250.0)")
