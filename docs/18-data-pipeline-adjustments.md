# 18. Data Pipeline & Licensing Adjustments (Hackathon V2)

*This document outlines the final production data pipeline adjustments made for the Meghdrishti V2 architecture, specifically addressing ECMWF commercial licensing and NOAA AWS S3 archival limits.*

---

## 1. The Operational Data vs. ERA5 Fallback
**The Core Philosophy:**
Meghdrishti's architecture is explicitly engineered to ingest noisy **Operational Data (OD)** (like NOAA GDAS or ECMWF Operational Analysis) during both training and inference. Training an AI on perfect, post-corrected reanalysis data (like ERA5) creates "Analysis Bias" — the model becomes falsely confident and fails catastrophically when deployed in live, noisy operational environments.

**The Licensing Reality (Hackathon Fallback):**
ECMWF strictly guards its historical Operational Data (MARS Database). Access is hard-locked to paying commercial clients, National Meteorological Services (like the IMD), and ECMWF Member States. 
Because our team cannot legally acquire a commercial MARS license for this hackathon, we have executed a **Production Fallback**:
* The Meghdrishti prototype is trained using **ERA5** initial conditions (via the open Copernicus CDS API).
* During the pitch, we will transparently state: *"The architecture is designed for Operational Data to prevent analysis bias. However, due to ECMWF commercial licensing restrictions on MARS, this prototype demonstrates the pipeline using ERA5. When handed over to the IMD, the pipeline is designed to simply flip the endpoint back to OD."*

## 2. K-Fold LOSO Temporal Shift (2021-2023)
**The Original Plan:**
We initially planned a 4-year dataset (2020-2023) to execute a 3-Fold Leave-One-Season-Out (LOSO) cross-validation (Training on 2020/2021, Validating on 2022, Testing on 2023).

**The NOAA AWS Reality:**
NOAA's open public AWS S3 bucket (`noaa-gfs-bdp-pds`) only began permanently archiving high-resolution GFS forecasts in late February 2021. 

**The Adjustment:**
We have officially shifted our temporal window to **2021-2023**.
* **Train:** Monsoon 2021, Monsoon 2022
* **Test (Holdout):** Monsoon 2023
This still provides 3 full years of dense, high-resolution data, perfectly satisfying the rigorous requirements for Leave-One-Season-Out (LOSO) validation to prove the AI can generalize to unseen years without overfitting.
