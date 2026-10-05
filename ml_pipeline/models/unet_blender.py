import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class ResBlock(nn.Module):
    """Residual Block to prevent vanishing gradients in deep networks."""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        # Use reflect padding to prevent coastal artifacts as per peer review
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, padding_mode='reflect', bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, padding_mode='reflect', bias=False)
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

class SpatioTemporalCrossAttention(nn.Module):
    """
    Replaces global FiLM. Allows network to dynamically scale features per-pixel 
    based on temporal queries (lead time, day of year).
    """
    def __init__(self, feature_dim, cond_dim=3, num_heads=4):
        super().__init__()
        self.num_heads = num_heads
        self.feature_dim = feature_dim
        
        # Project the scalar conditions into a Query vector
        self.query_proj = nn.Linear(cond_dim, feature_dim)
        
        # Multi-head attention (Query: Time, Key/Value: Spatial Features)
        self.attention = nn.MultiheadAttention(embed_dim=feature_dim, num_heads=num_heads, batch_first=True)
        self.norm = nn.LayerNorm(feature_dim)
        self.ffn = nn.Sequential(
            nn.Linear(feature_dim, feature_dim * 2),
            nn.ReLU(inplace=True),
            nn.Linear(feature_dim, feature_dim)
        )
        self.norm2 = nn.LayerNorm(feature_dim)

    def forward(self, x, condition):
        # x: [Batch, Channels, H, W]
        # condition: [Batch, cond_dim] (e.g. [LeadTime, Sin(Day), Cos(Day)])
        B, C, H, W = x.shape
        
        # Prepare Q: [Batch, 1, Channels]
        q = self.query_proj(condition).unsqueeze(1)
        
        # Prepare K, V: Flatten spatial dimensions to [Batch, H*W, Channels]
        kv = x.view(B, C, H * W).permute(0, 2, 1)
        
        # Cross Attention: time querying space
        attn_out, _ = self.attention(q, kv, kv) # Output: [Batch, 1, Channels]
        
        # We need to broadcast this attended temporal context back to the spatial grid
        # Reshape to [Batch, Channels, 1, 1] for broadcasting addition
        attn_context = attn_out.permute(0, 2, 1).unsqueeze(-1)
        
        # Add & Norm in spatial dimension
        out = x + attn_context
        # Apply FFN (pixel-wise)
        out_flat = out.view(B, C, H * W).permute(0, 2, 1)
        out_flat = self.norm(out_flat)
        ffn_out = self.ffn(out_flat)
        out_flat = self.norm2(out_flat + ffn_out)
        
        return out_flat.permute(0, 2, 1).view(B, C, H, W)

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
    def __init__(self, n_channels=13, n_models=2, features=[64, 128, 256, 512]):
        """
        Super-Resolution Spatial U-Net with Cross-Attention and 4 Variable Heads.
        
        Args:
            n_channels (int): Input channels (13: 2 models * 6 vars + 1 DEM)
            n_models (int): Models to blend (2: GFS, AI)
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

        # Bottleneck with Spatio-Temporal Cross Attention
        self.bottleneck = ResBlock(features[-1], features[-1]*2)
        self.cross_attn = SpatioTemporalCrossAttention(feature_dim=features[-1]*2, cond_dim=3)

        # Decoder with Attention Gates
        for feature in reversed(features):
            self.ups.append(nn.ConvTranspose2d(feature*2, feature, kernel_size=2, stride=2))
            self.attention_gates.append(AttentionGate(F_g=feature, F_l=feature, F_int=feature // 2))
            self.ups.append(ResBlock(feature*2, feature))

        # 4 Multi-Variable Output Heads
        # Each outputs (n_models + 1) channels: Softmax weights + Residual Bias
        out_dim = n_models + 1 
        self.head_rain = nn.Conv2d(features[0], out_dim, kernel_size=1)
        self.head_temp = nn.Conv2d(features[0], out_dim, kernel_size=1)
        self.head_wind_u = nn.Conv2d(features[0], out_dim, kernel_size=1)
        self.head_wind_v = nn.Conv2d(features[0], out_dim, kernel_size=1)

    def forward(self, x, condition):
        """
        x: [Batch, 13, H, W]
        condition: [Batch, 3] (Lead time, Sin(Day), Cos(Day))
        """
        skip_connections = []

        # Encoder
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)

        # Bottleneck + Cross-Attention
        x = self.bottleneck(x)
        x = self.cross_attn(x, condition) 
        
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

        # Output Heads (Slice into weights and residual)
        # Apply softmax only to the weights (first n_models channels)
        def process_head(head_out):
            weights = torch.softmax(head_out[:, :self.n_models, :, :], dim=1)
            residual = head_out[:, self.n_models:, :, :]
            return weights, residual

        w_rain, res_rain = process_head(self.head_rain(x))
        w_temp, res_temp = process_head(self.head_temp(x))
        w_wind_u, res_wind_u = process_head(self.head_wind_u(x))
        w_wind_v, res_wind_v = process_head(self.head_wind_v(x))

        return (w_rain, res_rain), (w_temp, res_temp), (w_wind_u, res_wind_u), (w_wind_v, res_wind_v)
