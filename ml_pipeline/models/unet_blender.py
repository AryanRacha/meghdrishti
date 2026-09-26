import torch
import torch.nn as nn
import torch.nn.functional as F

class DoubleConv(nn.Module):
    """(convolution => [BN] => ReLU) * 2"""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)

class UNetBlender(nn.Module):
    def __init__(self, n_channels, n_models=2, features=[64, 128, 256, 512]):
        """
        Spatial U-Net to predict blending weights for multiple forecast models.
        
        Args:
            n_channels (int): Number of input channels (e.g., GFS + AI_Model + Topography + Lead_Time = 4)
            n_models (int): Number of output channels (representing the weight maps for each base model, e.g., 2)
            features (list): Number of feature maps at each level of the U-Net.
        """
        super(UNetBlender, self).__init__()
        self.n_channels = n_channels
        self.n_models = n_models
        
        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # Encoder (Down part)
        in_channels = n_channels
        for feature in features:
            self.downs.append(DoubleConv(in_channels, feature))
            in_channels = feature
            
        # Bottleneck
        self.bottleneck = DoubleConv(features[-1], features[-1]*2)
        
        # Decoder (Up part)
        for feature in reversed(features):
            self.ups.append(
                nn.ConvTranspose2d(feature*2, feature, kernel_size=2, stride=2)
            )
            self.ups.append(DoubleConv(feature*2, feature))
            
        # Final output layer
        self.outc = nn.Conv2d(features[0], n_models, kernel_size=1)

    def forward(self, x):
        skip_connections = []
        
        # Run through encoder
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)
            
        x = self.bottleneck(x)
        skip_connections = skip_connections[::-1]
        
        # Run through decoder
        for idx in range(0, len(self.ups), 2):
            x = self.ups[idx](x)
            skip_connection = skip_connections[idx//2]
            
            # Handling odd spatial dimensions during upsampling
            if x.shape != skip_connection.shape:
                x = F.interpolate(x, size=skip_connection.shape[2:], mode="bilinear", align_corners=True)
                
            concat_skip = torch.cat((skip_connection, x), dim=1)
            x = self.ups[idx+1](concat_skip)
            
        # Output weights for each model
        logits = self.outc(x)
        
        # Apply Spatial Softmax so the weights for the models sum to 1.0 at every pixel
        weight_maps = torch.softmax(logits, dim=1)
        
        return weight_maps

if __name__ == '__main__':
    # Unit Test for U-Net Blender
    # Example: 4 Input Channels (GFS, GraphCast, DEM, LeadTime)
    # Output: 2 Channels (Weight for GFS, Weight for GraphCast)
    # Grid size: 128x128
    
    dummy_input = torch.randn(4, 4, 128, 128) # Batch=4, Channels=4, H=128, W=128
    model = UNetBlender(n_channels=4, n_models=2)
    
    # Test on CUDA if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Testing on device: {device}")
    model = model.to(device)
    dummy_input = dummy_input.to(device)
    
    output_weights = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output_weights.shape} (Expected: 4, 2, 128, 128)")
    
    # Verify weights sum to 1.0 across the channel dimension
    sums = torch.sum(output_weights, dim=1)
    print(f"Min sum: {sums.min().item()}, Max sum: {sums.max().item()} (Both should be 1.0)")
