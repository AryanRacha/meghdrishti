# Meghdrishti: SIH Presentation & Video Script Guide

*Use this document to structure your PowerPoint slides and your final video submission. It is broken down into high-impact, easy-to-understand points that directly address the SIH grading rubric.*

---

## Slide 1: The Problem (The "Smoothing" Trap)
* **Visual:** Show a map of India. Show a physical model (GFS) predicting a storm slightly to the left, and an AI model predicting it slightly to the right.
* **The Pitch:** The India Meteorological Department (IMD) currently blends different weather models together using simple linear statistics (Weighted Averages). 
* **The Fatal Flaw:** When you mathematically average two models that disagree on a storm's location, the storm gets "smoothed out" into a wide, harmless drizzle. Traditional statistics literally erase the exact extreme disasters (cloudbursts, cyclones) we are trying to predict.

## Slide 2: The Solution (Meghdrishti)
* **Visual:** A flowchart showing GFS + Pangu-Weather entering our "Super-UNet Brain", resulting in a highly accurate, high-resolution map of India.
* **The Pitch:** Meghdrishti is a PyTorch-powered Super-Resolution Deep Learning engine. Instead of a blanket average, our AI looks at 13 atmospheric variables—including pressure, humidity, and the mountains of India—and dynamically assigns "Trust Weights" pixel-by-pixel. It knows to trust physical physics over the Himalayas, but trusts AI over the plains.

## Slide 3: The Architecture (How it Works)
* **Visual:** A simplified diagram of the U-Net. (Encoder -> Cross-Attention -> Decoder -> 4 Output Heads).
* **The Pitch:** 
    1. **Super-Resolution:** We upscale standard 25km forecasts into a highly dense 10km grid to match the IMD's sovereign observation data.
    2. **Cross-Attention:** Our AI is "Time-Aware." It dynamically changes its blending strategy depending on whether it is predicting tomorrow's weather or next week's weather.
    3. **The Safety Valve:** We built a "Residual Bias Head." If both the physical model and the AI model completely miss a storm, our AI can physically inject rain into the final forecast because it recognized the dropping pressure and rising humidity.

## Slide 4: Solving the Data Trap (Why Our AI is Production-Ready)
* **Visual:** A side-by-side of "Perfect Lab Data" vs "Noisy Real-World Data."
* **The Pitch:** Most teams train their AI on perfect, post-corrected reanalysis data (ERA5). This causes the AI to fail catastrophically in the real world when it encounters live, noisy data. We trained Meghdrishti using historical **noisy operational data (GDAS)**. Our system is battle-tested for live production, not just a hackathon lab.

## Slide 5: The Secret Weapon (Extreme-Weighted Loss)
* **Visual:** A graph showing a massive spike in rainfall. Show the AI dedicating 100% of its focus to that spike.
* **The Pitch:** India is dry for 8 months of the year. Standard AI models become numb to rain. We engineered a **Masked Extreme-Weighted Loss Function**. Our neural network is only punished for mistakes it makes during actual rain events, and the punishment scales exponentially for severe cloudbursts (>64.5mm). 100% of the AI's learning capacity is dedicated to predicting high-impact extreme weather.

## Slide 6: The Command Center (Frontend Demo)
* **Visual:** Screen recording of the React UI.
* **The Pitch:** The model's brain is connected to a lightning-fast React + FastAPI dashboard. Meteorologists can instantly compare the raw physical model, the raw AI model, and the Meghdrishti Blend side-by-side, complete with automated Extreme Weather Alerts for vulnerable districts.

---

## 🎬 Video Submission Tips
1. **First 30 Seconds:** Do not waste time on team introductions. Start immediately with: *"IMD's current blending methods erase extreme weather. We built a 13-channel PyTorch U-Net to fix it."*
2. **The "Tech Flex":** Make sure to mention **Spatio-Temporal Cross-Attention**, **Super-Resolution ($320 \times 320$)**, and the **Leave-One-Season-Out (LOSO)** validation. Judges love seeing rigorous academic terminology applied practically.
3. **The Proof:** Show a screenshot of the `evaluation_report.json` or the terminal output where our Super-UNet mathematically beats the Simple Average baseline in the Extreme Dependency Index (EDI). 
