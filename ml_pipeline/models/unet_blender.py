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

class AttentionGate(nn.Module):
    """Filters skip connections to focus on relevant spatial features (e.g., topography)."""
    def __init__(self, F_g, F_l, F_int):
        super(AttentionGate, self).__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g, F_int, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(F_int)
        )
        self.W_x = nn.Sequential(
            nn.Conv2d(F_l, F_int, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(F_int)
        )
        self.psi = nn.Sequential(
            nn.Conv2d(F_int, 1, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, g, x):
        g1 = self.W_g(g)
        x1 = self.W_x(x)

        # Handle spatial dimension mismatches gracefully
        if g1.shape[2:] != x1.shape[2:]:
            g1 = F.interpolate(g1, size=x1.shape[2:], mode="bilinear", align_corners=True)

        psi = self.relu(g1 + x1)
        psi = self.psi(psi)
        return x * psi

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
        self.attention_gates = nn.ModuleList() # New ModuleList for AGs
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # Encoder (Down part)
        in_channels = n_channels
        for feature in features:
            self.downs.append(DoubleConv(in_channels, feature))
            in_channels = feature

        # Bottleneck
        self.bottleneck = DoubleConv(features[-1], features[-1]*2)

        # Decoder (Up part) with Attention Gates
        for feature in reversed(features):
            self.ups.append(
                nn.ConvTranspose2d(feature*2, feature, kernel_size=2, stride=2)
            )
            # F_g (from upsample) = feature, F_l (from encoder) = feature
            self.attention_gates.append(
                AttentionGate(F_g=feature, F_l=feature, F_int=feature // 2)
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
        for idx in range(len(self.attention_gates)):
            gating_signal = self.ups[idx*2](x) # Up-conv layer
            skip_connection = skip_connections[idx]

            if gating_signal.shape != skip_connection.shape:
                gating_signal = F.interpolate(gating_signal, size=skip_connection.shape[2:], mode="bilinear", align_corners=True)

            # Apply attention gate before concatenation
            attended_skip = self.attention_gates[idx](gating_signal, skip_connection)

            concat_skip = torch.cat((attended_skip, gating_signal), dim=1)
            x = self.ups[idx*2 + 1](concat_skip) # DoubleConv layer

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
