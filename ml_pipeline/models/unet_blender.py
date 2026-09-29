import torch
import torch.nn as nn
import torch.nn.functional as F

class ResBlock(nn.Module):
    """Residual Block to prevent vanishing gradients in deep networks."""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        # Skip connection adjustment if channels change
        self.skip = nn.Sequential()
        if in_channels != out_channels:
            self.skip = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        identity = self.skip(x)
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += identity
        return self.relu(out)

class FiLMLayer(nn.Module):
    """Feature-wise Linear Modulation to inject Lead Time / Season temporally."""
    def __init__(self, num_features, cond_dim=1):
        super().__init__()
        # MLPs to learn gamma (scale) and beta (shift) from the scalar temporal condition
        self.gamma = nn.Linear(cond_dim, num_features)
        self.beta = nn.Linear(cond_dim, num_features)

    def forward(self, x, condition):
        # condition is [Batch, cond_dim] (e.g. Lead time in hours)
        g = self.gamma(condition).unsqueeze(-1).unsqueeze(-1) # Shape: [Batch, Features, 1, 1]
        b = self.beta(condition).unsqueeze(-1).unsqueeze(-1)
        return (1 + g) * x + b

class AttentionGate(nn.Module):
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
        if g1.shape[2:] != x1.shape[2:]:
            g1 = F.interpolate(g1, size=x1.shape[2:], mode="bilinear", align_corners=True)
        psi = self.relu(g1 + x1)
        psi = self.psi(psi)
        return x * psi

class SuperUNetBlender(nn.Module):
    def __init__(self, n_channels, n_models=6, features=[64, 128, 256, 512]):
        """
        Super-Ensemble Spatial U-Net with FiLM and 3 Variable Heads.
        
        Args:
            n_channels (int): Input channels (6 models * 3 variables + 1 DEM = 19 channels)
            n_models (int): Output classes per head (6 models to blend)
        """
        super(SuperUNetBlender, self).__init__()
        self.n_models = n_models
        
        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        self.attention_gates = nn.ModuleList()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        # Encoder using ResBlocks
        in_channels_curr = n_channels
        for feature in features:
            self.downs.append(ResBlock(in_channels_curr, feature))
            in_channels_curr = feature

        # Bottleneck with FiLM Temporal Injection
        self.bottleneck = ResBlock(features[-1], features[-1]*2)
        self.film = FiLMLayer(num_features=features[-1]*2, cond_dim=1) # Cond_dim=1 for Lead Time

        # Decoder with Attention Gates
        for feature in reversed(features):
            self.ups.append(nn.ConvTranspose2d(feature*2, feature, kernel_size=2, stride=2))
            self.attention_gates.append(AttentionGate(F_g=feature, F_l=feature, F_int=feature // 2))
            self.ups.append(ResBlock(feature*2, feature))

        # 3 Multi-Variable Output Heads
        # Each outputs a weight map for the 6 models
        self.head_rain = nn.Conv2d(features[0], n_models, kernel_size=1)
        self.head_temp = nn.Conv2d(features[0], n_models, kernel_size=1)
        self.head_wind = nn.Conv2d(features[0], n_models, kernel_size=1)

    def forward(self, x, lead_time):
        """
        x: [Batch, 19, H, W]
        lead_time: [Batch, 1]
        """
        skip_connections = []

        # Encoder
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)

        # Bottleneck + FiLM
        x = self.bottleneck(x)
        x = self.film(x, lead_time) # Inject time dynamics!
        
        skip_connections = skip_connections[::-1]

        # Decoder
        for idx in range(len(self.attention_gates)):
            gating_signal = self.ups[idx*2](x)
            skip_connection = skip_connections[idx]

            if gating_signal.shape != skip_connection.shape:
                gating_signal = F.interpolate(gating_signal, size=skip_connection.shape[2:], mode="bilinear", align_corners=True)

            attended_skip = self.attention_gates[idx](gating_signal, skip_connection)
            concat_skip = torch.cat((attended_skip, gating_signal), dim=1)
            x = self.ups[idx*2 + 1](concat_skip)

        # Output Heads (Softmax across the models dimension so weights sum to 1.0)
        weights_rain = torch.softmax(self.head_rain(x), dim=1)
        weights_temp = torch.softmax(self.head_temp(x), dim=1)
        weights_wind = torch.softmax(self.head_wind(x), dim=1)

        return weights_rain, weights_temp, weights_wind
