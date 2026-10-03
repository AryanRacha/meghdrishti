# 17. Evaluation Methodology

*This document explains in simple terms how we grade Meghdrishti. Weather models are notoriously difficult to evaluate because traditional math often penalizes models for doing the right thing. Here is how we verify our AI is actually production-ready.*

---

## 1. The "Smoothing" Problem (Why Standard Math Fails)
Imagine a massive cyclone hitting Mumbai. 
* Model A predicts the cyclone hits Mumbai perfectly, but misses the exact landfall by 10 kilometers.
* Model B completely misses the cyclone and predicts a light, uniform drizzle across all of Maharashtra.

Using standard Mean Squared Error (MSE) — the most common ML metric — **Model B will get a better score**. Why? Because predicting a "light drizzle everywhere" minimizes the average mathematical error, whereas missing a massive cyclone by just 10 kilometers creates a massive mathematical error spike. 

This is why traditional statistics cause weather models to "smooth out." If we want Meghdrishti to predict extreme disasters, we cannot use standard math.

---

## 2. Our WMO-Standard Verification Metrics
To prove Meghdrishti works, we use the exact metrics established by the World Meteorological Organization (WMO) and the India Meteorological Department (IMD).

### Continuous Metrics (The Baselines)
We do track the basics to ensure the model isn't hallucinating:
* **RMSE (Root Mean Square Error):** Measures the overall average error magnitude.
* **MAE (Mean Absolute Error):** Similar to RMSE, but less punishing to outliers.
* **Bias:** Tells us if our model is systematically over-predicting (too wet) or under-predicting (too dry).
* **ACC (Anomaly Correlation Coefficient):** *The Gold Standard.* It measures whether the shape and pattern of the weather system match reality, even if the exact numbers are slightly off. If ACC > 0.6, the forecast is considered "skillful."

### Categorical Extreme Metrics (The Pitch Winners)
We divide the rainfall into IMD's official categories (Light, Moderate, Heavy >64.5mm, Extremely Heavy >204.5mm). For each threshold, we calculate a "Contingency Table" (Hits, Misses, False Alarms), yielding:

* **POD (Probability of Detection):** Out of all the actual cloudbursts, what percentage did we catch? (Also known as Hit Rate).
* **FAR (False Alarm Ratio):** Out of all the cloudbursts we predicted, how many were false alarms?
* **CSI (Critical Success Index):** A balanced score combining POD and FAR. It explicitly ignores "Correct Negatives" (days where we correctly predicted no rain) because predicting "no rain" in the dry season is too easy and inflates the score.
* **ETS (Equitable Threat Score):** Similar to CSI, but it mathematically subtracts "random chance." If you just guessed randomly, you'd get some hits. ETS removes those lucky guesses to show true AI skill.
* **EDI (Extreme Dependency Index):** As weather events get more extreme (like a 1-in-100-year storm), all math scores naturally degrade to zero. EDI is a special logarithmic formula that does not degrade, allowing us to accurately score the model on the rarest, most catastrophic events.

---

## 3. Multilateral Benchmarking (The Proof)
We don't just calculate these scores for Meghdrishti. Every time we evaluate, we calculate the scores for 4 distinct streams side-by-side:
1. **Raw GFS (Physics)**
2. **Raw Pangu-Weather (AI)**
3. **Simple Ensemble Mean (IMD's current method)**
4. **Meghdrishti (Our Super-UNet)**

By showing the judges that Meghdrishti has a higher EDI and ETS score specifically in the "Heavy Rainfall" category compared to the Simple Ensemble Mean, we mathematically prove that we have solved the smoothing problem.

---

## 4. Spatio-Temporal Spatial Masking
India is a massive subcontinent with completely different climate zones. Evaluating the entire country at once hides the nuances of the AI's blending strategy.

Our evaluation suite uses **Spatial Masks**:
1. **The Himalayas / Western Ghats (Orography):** AI models struggle heavily with mountains. We isolate these pixels to prove our U-Net dynamically learns to shift its trust back to the physical GFS model in mountainous terrain.
2. **Coastal / Arabian Sea:** We isolate coastal pixels to evaluate cyclonic activity.
3. **The Plains:** We evaluate central India to show how well the AI captures monsoon troughs.

By evaluating the model regionally, we prove to the judges that the Neural Network has genuinely learned the geography of India, rather than just blindly memorizing numbers.
