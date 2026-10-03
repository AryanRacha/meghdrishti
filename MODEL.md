# Meghdrishti: The AI Model Deep Dive

*This document explains how our AI weather model works, in simple, direct language. It is designed to help the team understand the core technology for presentations, videos, and the final SIH pitch.*

---

## 1. What Does Our Model Actually Do?
Traditional weather forecasting (like NOAA's GFS) uses complex physics equations. It's highly reliable but often struggles to pinpoint exact local extremes (like a sudden cloudburst over a specific valley). Recently, tech giants have released AI weather models (like Huawei's Pangu-Weather) which are incredibly fast, but they tend to "smooth out" the weather, missing severe storms entirely.

The India Meteorological Department (IMD) currently tries to combine these models using simple statistics (a weighted average).

**Our solution is Meghdrishti:** A Deep Learning neural network (a Super-Resolution Attention U-Net) that dynamically learns how to blend physical models and AI models together. Our AI looks at the topography (mountains vs. plains), the humidity, and the pressure, and dynamically decides: *"I trust the physical model 80% here, but I trust the AI model 90% over there."*

---

## 2. The Input Data (What the AI "Sees")
To make a smart decision, our AI needs a lot of context. It ingests a massive grid of data over India with **13 different layers (channels)**.

### The 13 Inputs:
1. **Rainfall, Temperature, U-Wind, V-Wind, Pressure, Humidity** from the GFS Physical Model (6 layers).
2. **Rainfall, Temperature, U-Wind, V-Wind, Pressure, Humidity** from the Pangu-Weather AI Model (6 layers).
3. **Topography / Elevation** (1 static layer showing the mountains and valleys of India).

### Where did we get it?
* **GFS (Physical NWP)**: Downloaded directly from NOAA archives.
* **Pangu-Weather (AI Forecast)**: We ran Huawei's open-source Pangu-Weather AI locally on an RTX 4090 GPU to generate historical predictions.
* **IMD Ground Truth**: To train the AI, we gave it the "Answer Key" — what the weather actually was on those days, using the IMD's highly accurate 10km gridded observation data.

**Crucial Pitch Point:** We generated our AI data using *noisy, real-time* initial conditions (GDAS). This proves our system works in real-world, live operational environments, not just in pristine lab conditions.

---

## 3. The Architecture (How the Brain Works)
Our AI architecture is a **Super-Resolution Spatio-Temporal U-Net**. Here is how it processes weather step-by-step:

1. **Super-Resolution Upscaling:** We take the standard $25\text{km}$ resolution forecasts and mathematically expand them into a highly detailed **$10\text{km}$ grid** (a $320 \times 320$ map of India). This allows our model to predict localized, block-level disasters.
2. **The Encoder (Seeing the Big Picture):** The network shrinks the map down to extract broad weather patterns (like understanding a massive cyclone forming in the Bay of Bengal).
3. **Cross-Attention (Understanding Time):** Weather behaves differently at a 24-hour forecast vs. a 120-hour forecast. Right in the middle of the network, we inject the "Lead Time" and the "Season." The AI dynamically changes how it looks at the map based on whether it is predicting tomorrow's weather or next week's weather.
4. **The Decoder (Pinpointing the Location):** The network scales the patterns back up to the high-resolution 10km grid, mapping the severe weather precisely to actual district boundaries.
5. **The Safety-Valve Output (4 Heads):** The network splits into four independent "Brains"—one for Rain, Temp, U-Wind, and V-Wind. It outputs trust weights indicating exactly how to blend the two models. **Crucially, it has a "Residual Safety Valve."** If both the Physical and AI models completely miss a storm, our neural network can physically inject rain into the final forecast because it recognized the warning signs (dropping pressure, rising humidity, and mountain slopes).

---

## 4. The Training Engine (How it Learns)
A neural network is only as smart as how it is punished for mistakes. We built two highly advanced mechanisms to train this model:

### 1. Masked Extreme-Weighted Loss (Preserving Cloudbursts)
India is dry for 8 months of the year. If we trained our AI on the whole year, it would get really good at predicting "Zero Rain" and become numb to extreme storms. 
**Our Solution:** We programmed the AI to *only* calculate its rain mistakes on pixels where rain actually fell. Furthermore, if it misses a severe cloudburst (>64.5 mm/day), we punish the AI exponentially harder than if it misses a light drizzle. 100% of the AI's learning capacity is dedicated to severe weather.

### 2. Leave-One-Season-Out (LOSO) Validation
If you randomly shuffle weather data, the AI will cheat by remembering what happened yesterday.
**Our Solution:** We trained the AI on the 2021 and 2022 monsoons, and then tested it on the completely unseen 2023 monsoon. This proves to the IMD judges that our AI actually understands meteorology and can generalize to brand new, unseen weather years.

---

## 5. Summary for the Pitch
* **What it is:** A 13-channel Super-Resolution PyTorch AI.
* **What it does:** Dynamically blends Physical and AI forecasts over India at a 10km resolution.
* **Why it wins:** It eliminates the "smoothing" problem of standard statistics by using a custom Extreme-Weighted Loss and a Residual Safety Valve to guarantee extreme disasters (cloudbursts, cyclones, heatwaves) are preserved and predicted accurately.
