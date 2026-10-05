# Meghdrishti: The AI Model Deep Dive (V2 Master Blueprint)

*This document is the definitive, multi-stage breakdown of the Meghdrishti V2 system. It details exactly how the data flows, the sequential stacking of the neural network architecture, and the mathematical optimizations applied at each step to ensure production-grade accuracy for the India Meteorological Department (IMD).*

---

## Stage 1: The Data Layer (Sourcing & Practical Adjustments)

Before any PyTorch tensors are created, the raw atmospheric data is sourced. We made specific, calculated adjustments to fit within open-source licensing limits while maintaining operational integrity.

*   **The Duration (Adjusted):** 3 Monsoon seasons (2021–2023). NOAA's public AWS S3 archives only began permanently storing high-resolution GFS forecasts in late February 2021. This provides a massive, clean 3-year block for training and validation.
*   **The Ground Truth (Answer Key):** The official **IMD $0.1^\circ$ Gridded Datasets** (~10km resolution). ERA5 is used as the fallback if IMD data is unavailable.
*   **Model 1 (Physics Base):** NOAA GFS Operational Forecasts, downloaded at $0.25^\circ$.
*   **Model 2 (AI Base):** Huawei Pangu-Weather, generated locally on an RTX 4090 via the `ai-models` package.
*   **Analysis Bias Prevention:** Operationally, Pangu-Weather should be initialized with noisy NOAA GDAS/ECMWF Operational Data (OD). However, ECMWF MARS operational data is locked behind a commercial paywall. For this hackathon prototype, we use **ERA5** to initialize the AI, but the pipeline is explicitly designed to ingest noisy OD in a live IMD environment. This prevents the blending model from blindly over-trusting the AI during training, an error known as "Analysis Bias."

---

## Stage 2: Preprocessing & Ingestion (Data Hygiene)

The raw forecasts undergo strict mathematical hygiene before entering the U-Net.

### 1. Spatial Super-Resolution Alignment
*   **Why we did this:** Raw models predict at $25\text{km}$ resolution ($0.25^\circ$). IMD requires localized $10\text{km}$ resolution ($0.1^\circ$). Evaluating a $25\text{km}$ prediction against a $10\text{km}$ ground truth warps the geography.
*   **What it does:** Mathematically expands low-resolution grids to perfectly match high-resolution observation grids.
*   **How it does it:** We subset a perfect $32^\circ \times 32^\circ$ geographic bounding box around India ($6^\circ\text{–}38^\circ\text{N}$, $66^\circ\text{–}98^\circ\text{E}$). We apply Bilinear Interpolation, taking the 4 nearest $25\text{km}$ pixels to calculate a smooth, weighted average, generating a dense **$320 \times 320$ tensor** of $10\text{km}$ pixels.

### 2. Vector Deconstruction (Wind Splitting)
*   **Why we did this:** Blending "Wind Magnitude" is physically illegal (a $15\text{m/s}$ East wind and a $15\text{m/s}$ West wind should cancel to zero, not add up).
*   **What it does:** Provides physically compliant wind kinematics.
*   **How it does it:** We mathematically split the wind magnitude into its raw vectors: **10m U-Wind (Zonal/East-West)** and **10m V-Wind (Meridional/North-South)**. Magnitude is calculated only as a deterministic post-processing step.

### 3. Z-Score vs. MinMax Normalization
*   **Why we did this:** Neural networks struggle with raw numbers of vastly different scales (e.g., Temperature at $300\text{K}$ vs Rainfall at $0.5\text{mm}$). Gradients would be dominated by Temperature. However, standard Z-Score normalization on Relative Humidity (RH) is dangerous—it does not enforce hard boundaries, allowing physically impossible humidity levels (e.g., $115\%$) which break the network's atmospheric physics.
*   **What it does:** Balances all input channels equally while strictly enforcing the laws of physics for bounded variables.
*   **How it does it:**
    *   **Z-Score (Rain, Temp, Wind, MSLP):** Calculates the mean and standard deviation of the batch, using `(x - mean) / std`. This centers data at $0$ with a variance of $1$, allowing extreme outliers (like a pressure drop) to stretch outward naturally without capping.
    *   **MinMax Scaling (Relative Humidity):** Explicitly clamps raw humidity between $0.0$ and $100.0$, applying `(x - min) / (max - min)`. This squashes humidity strictly between $[0.0, 1.0]$. The neural network is mathematically guaranteed to never process a physical impossibility.

### 4. The 13-Channel Input Tensor
*   **Why we did this:** You cannot predict a cloudburst simply by looking at previous rainfall; the network needs atmospheric context like humidity and pressure.
*   **What it does:** Provides a full-context picture of the atmosphere.
*   **How it does it:** We stack the 6 variables from GFS (Rain, Temp, U-Wind, V-Wind, MSLP, RH), the 6 variables from the AI, and 1 static Topography (DEM) map. The final tensor shape entering the U-Net is `[Batch, 13, 320, 320]`.

---

## Stage 3: The Super-UNet Architecture (Component Sequence)

The `[Batch, 13, 320, 320]` tensor flows sequentially through the PyTorch `SuperUNetBlender`:

### 1. The Encoder (Downsampling via ResBlocks & Reflection Padding)
*   **Why we did this:** Standard deep networks lose mathematical signal (the "vanishing gradient" problem). Furthermore, standard convolutions pad map edges with "Zeros," which the network interprets as $0^\circ\text{C}$ and perfectly dry, causing cold artifacts to bleed into the Indian coastlines.
*   **What it does:** Safely learns deep, complex weather patterns while maintaining the physical integrity of coastlines.
*   **How it does it:** The grid passes through 4 Convolutional `ResBlocks` and `MaxPool2d` layers.
    *   *ResBlocks:* Uses a Skip Connection ($F(x) + x$), adding the block's input directly to its output. The network learns the *difference* (residual) rather than relearning the whole image.
    *   *Reflection Padding:* `padding_mode='reflect'` mirrors the actual coastal weather values outward (if the coast is $30^\circ\text{C}$, the padding is $30^\circ\text{C}$), preventing artificial temperature drops.
    *   *Downsampling:* Shrinks the grid, allowing the network to extract deep, broad atmospheric features (like a monsoon trough).

### 2. The Bottleneck (Spatio-Temporal Cross-Attention)
*   **Why we did this:** Weather behaves differently depending on the time of year (Monsoon vs. Winter) and the forecast horizon (Day 1 vs. Day 5). The network must dynamically alter its blending strategy based on time, not just geography.
*   **What it does:** Acts as the "Brain" at the deepest part of the network, scaling geographic features based on temporal awareness.
*   **How it does it:** We extract Time `[Lead Time, Sin(Day), Cos(Day)]` and project it into a **Query (Q)** vector. The flattened spatial map is projected into **Key (K)** and **Value (V)** vectors. The network calculates the dot product between Q and K to yield an "Attention Score" (e.g., *How much does this Himalayan pixel care that it is August?*). It multiplies this score by V, dynamically scaling the pixel's importance based on the time of year.

### 3. The Decoder (Upsampling via Attention Gates)
*   **Why we did this:** As the network scales back up to high resolution, it wastes massive computing power analyzing "empty skies" or irrelevant background noise (like the open ocean).
*   **What it does:** Acts as a spatial spotlight, telling the network where to focus and what background noise to suppress.
*   **How it does it:** The `AttentionGate` merges deep, broad features (from the Bottleneck) with high-res details saved via Skip Connections (from the Encoder). It applies a Sigmoid activation to create a multiplier map (strictly between $0.0$ and $1.0$). It multiplies this map against the high-res features. Empty skies get suppressed ($0.01$), while forming cyclones are highlighted ($0.99$).

### 4. The Output Heads (Softmax + Residual Bias)
*   **Why we did this:** We need the network to output trust percentages (e.g., 70% GFS, 30% AI). However, if both GFS and AI predict $0\text{mm}$ of rain, the blend equals $0\text{mm}$. The network needs a "Safety Valve" to physically inject rain into the forecast if it knows both models are wrong.
*   **What it does:** Outputs mathematically stable blending weights while retaining the power to override the models entirely.
*   **How it does it:** The network splits into 4 distinct variable heads (Rain, Temp, U-Wind, V-Wind).
    *   *Softmax:* Each head outputs raw trust scores for GFS and AI. The Softmax function ($e^x / \sum e^x$) forces these scores to sum perfectly to $1.0$, creating percentages.
    *   *Residual Bias:* A 3rd channel ($\Delta_{\text{residual}}$) bypasses Softmax entirely. The final math is: `(GFS * Weight_GFS) + (AI * Weight_AI) + Residual_Bias`. If the network detects dropping pressure and rising humidity over a mountain, it uses this raw numeric bias to add $50\text{mm}$ of rain to the final forecast, overriding the flawed inputs.

---

## Stage 4: The Training Engine (Loss & Validation)

### 1. The Masked Extreme-Weighted Loss
*   **Why we did this:** India is dry for 8 months of the year. Standard MSE punishes all mistakes equally, forcing the network to optimize for predicting "Zero Rain" and completely ignore rare, catastrophic cloudbursts.
*   **What it does:** Forces the network to dedicate 100% of its learning capacity to extreme weather events, ignoring dry days.
*   **How it does it:**
    *   *The Mask:* Generates a boolean tensor `(target > 0.1) | (prediction > 0.1)`. Any pixel completely dry in both reality and prediction is multiplied by $0$, preventing gradients from drifting toward "zero" during winter.
    *   *The Penalty:* For rainy pixels, it calculates the base MSE. If the Target crosses IMD's Heavy threshold ($>64.5\text{mm}$), it calculates an exponential multiplier: `1.0 + alpha * exp(beta * (Target - 64.5) / 64.5)`. Missing a 150mm cloudburst results in a massive gradient explosion, ruthlessly forcing the network to adjust its weights.

### 2. Sequential FP16 Backprop (Numerical Stability)
*   **Why we did this:** To balance Temp (large numbers) and Rain (small numbers), we must multiply the Temp loss by $0.01$. In Mixed Precision (FP16), multiplying a small gradient by $0.01$ causes the 16-bit float to `underflow` (round to absolute zero). The network literally stops learning temperature.
*   **What it does:** Balances multi-task learning perfectly without math crashing to zero.
*   **How it does it:** Instead of pre-scaling losses, we use the PyTorch computation graph. We call `scaler.scale(loss_rain).backward(retain_graph=True)`. The GPU scales the rain gradients up to a safe 16-bit size, calculates, and stores them. We repeat this for Temp and Wind independently, allowing the GPU to calculate each task's gradients at their full, native numeric size before stepping the optimizer.

### 3. Leave-One-Season-Out (LOSO) Validation
*   **Why we did this:** If you randomly shuffle 3 years of weather data, Day 1 (Train) and Day 2 (Test) are too similar. The network scores highly just by guessing the weather is the same as yesterday.
*   **What it does:** Proves the AI actually understands meteorology and can generalize to completely alien, unseen weather years.
*   **How it does it:** We enforce a hard temporal wall. We isolate the entire 2021 and 2022 Monsoons strictly for training. We isolate the entire 2023 Monsoon strictly for testing, forcing the model to predict 2023 without ever having seen a single day of it.

---

## Stage 5: The Evaluation Engine (Proving the Model Works)

Standard ML math (MSE) actively punishes models for predicting rare extreme events. A model predicting a uniform light drizzle will score better than a model missing a massive cyclone by 10km. We evaluate Meghdrishti using custom WMO and IMD metrics to prove we solved this "Smoothing" problem.

### 1. Categorical Extreme Metrics (ETS & EDI)
*   **Why we did this:** We need to accurately score the model's ability to predict catastrophic events (like cloudbursts), ignoring minor millimeter differences.
*   **What it does:** Converts continuous rain into binary IMD categories (e.g., Heavy $>64.5\text{mm}$) to calculate Hits and False Alarms.
*   **How it does it:**
    *   **ETS (Equitable Threat Score):** Calculates accuracy but mathematically subtracts $Hits_{random}$ (hits a model gets just by blindly guessing based on base-rate rain frequency). Reveals pure AI skill.
    *   **EDI (Extreme Dependency Index):** As events get rarer (a 1-in-100-year storm), standard scores crash to zero because the False Alarm Ratio dominates. EDI uses a logarithmic formula: `(log(FAR) - log(POD)) / (log(FAR) + log(POD))`. This stabilizes the score, legitimately proving we can predict catastrophic outliers.

### 2. Spatio-Temporal Masking
*   **Why we did this:** Evaluating India as a single block hides geographic nuances. AI models typically fail over complex terrain.
*   **What it does:** Proves the U-Net has physically learned the topography of India and dynamically alters its trust weights based on terrain.
*   **How it does it:** We use a static geographical mask (binary tensor of 1s and 0s) to isolate the Himalayas, the Coasts, and the Plains. We calculate the EDI score exclusively inside those masked pixels and compare it against Raw GFS, Raw AI, and the IMD's current Simple Ensemble Mean. By beating the Simple Mean in the EDI score specifically over complex terrain, we mathematically prove we have solved the smoothing problem.
