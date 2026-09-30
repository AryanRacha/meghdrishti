# 12 - Video Presentation & Pitch Strategy (SIH26081)

## 1. The Strategy: Defeating "Vibe-Coded" Projects

In hackathons like SIH, most teams submit "vibe-coded" prototypes: a nice React UI that calls a generic commercial weather API or wraps an LLM. MoES scientists and evaluators immediately discount these because they lack domain science and modeling rigor.

To stand out, your presentation must emphasize **engineering depth, mathematical rigor, and operational domain realism**:

| Vibe-Coded Prototype | Meghdrishti (Our Submission) | What You Must Emphasize in the Video |
| :--- | :--- | :--- |
| Calls external API / Gemini prompt | Real physical NWP grids (NOAA GFS 0.25°) + Copernicus ERA5 reanalysis | *"We process raw NetCDF/GRIB2 atmospheric grids cropped to the Indian subcontinent (8°–38°N, 68°–98°E)."* |
| Naive averaging: $\frac{\text{GFS} + \text{AI}}{2}$ | Deep learning Super-UNet predicting spatially dynamic per-pixel trust weights $w(x,y)$ | *"Simple averaging dilutes cloudburst signals. Our Super-UNet dynamically blends based on local topography and atmospheric physics."* |
| Standard MSE loss | **Custom Extreme-Weighted Loss**: $\mathcal{L} = (1 + \alpha \cdot y)(y - \hat{y})^2$ | *"Missing a drizzle has negligible cost; missing a 200 mm cloudburst kills people. Our custom loss exponentially penalizes missed extremes."* |
| Black-box colored maps | **Explainable AI (XAI)** Trust Maps + Interactive Pixel Inspector | *"Operational forecasters cannot trust black boxes. Every pixel exposes its mathematical decomposition equation."* |
| Generic weather forecast | **Impact-Based Decision Support**: Census GIS population exposure, 12 Indic TTS dialects, official IMD bulletin | *"We don't just predict rain—we tell District Magistrates which villages to evacuate, pre-position NDRF, and broadcast multilingual alerts."* |

---

## 2. Minute-by-Minute Video Pitch Script (Target: 3:00 – 3:30)

Use the built-in **Guided Tour (`▶ Guided Tour`)** and advance each step cleanly using the **`Enter`** key as you speak.

---

### Phase 1: The Core Scientific Problem (0:00 – 0:45)
- **Tour Steps**: `Meghdrishti` → `The problem` → `Super-UNet architecture` → `Extreme-weighted loss`
- **What to say**:
  > *"Respected jury, conventional weather forecasting in India faces a critical dilemma. Physics-based NWP models like NOAA GFS solve Navier-Stokes atmospheric equations—they capture large-scale monsoon dynamics but struggle with localized orographic cloudbursts. Modern AI models are computationally fast, but tend to over-smooth extreme peaks. If you simply average them, you completely dilute the extreme disaster signal.*
  >
  > *To solve this for the Ministry of Earth Sciences (SIH26081), we engineered **Meghdrishti**: a multi-variable Hybrid AI-NWP Blending System for precipitation, temperature, and wind, built around a custom Super-UNet with FiLM lead-time conditioning.*
  >
  > *Our winning edge is our **Custom Extreme-Weighted Loss Function**. Standard MSE optimizes for average error, ignoring rare disasters. Our loss scales penalties linearly and exponentially with precipitation intensity—ensuring the neural network treats preserving extreme cloudbursts as top priority."*

---

### Phase 2: Live Forecast Blending & Mathematical Explainability (0:45 – 1:45)
- **Tour Steps**: `Input 1 · GFS` → `Input 2 · AI` → `Output · Super-UNet blend` → `Side by side` → `Trust Map` → `XAI · Pixel Inspector`
- **What to say**:
  > *"Here is how it works on live operational data. We ingest 7 atmospheric channels cropped to the Indian bounding box. On the left is the raw GFS physics forecast; on the right is our Super-UNet blended output. Notice how the blended field sharpens the monsoon front while resolving local orographic precipitation in the Himalayan foothills.*
  >
  > *Crucially, operational meteorologists refuse black boxes. Meghdrishti features native **Explainability**. The Trust Map shows where the model relies on physics (teal) versus AI (violet). By clicking any 26-kilometer grid cell, our Pixel Inspector reveals the exact mathematical blending equation: $w_{\text{GFS}} \cdot \text{GFS} + w_{\text{AI}} \cdot \text{AI}$. The forecaster sees the exact weights, input values, and IMD classification behind every pixel."*

---

### Phase 3: Multi-Day Horizon & Spatio-Temporal Dynamics (1:45 – 2:15)
- **Tour Steps**: `Rain, temp & wind` → `Lead time · FiLM conditioning` → `Monsoon time-lapse`
- **What to say**:
  > *"Meghdrishti blends multiple atmospheric variables—precipitation, 2-meter temperature, and 10-meter wind vectors—each with dedicated per-variable trust heads.*
  >
  > *Using Feature-wise Linear Modulation (FiLM), the model dynamically shifts its blending policy as uncertainty compounds from Day 1 (+24h) out to Day 5 (+120h). Our multi-temporal engine provides seamless time-lapse progression across the entire monsoon season."*

---

### Phase 4: Impact-Based Forecasting & Disaster Action (2:15 – 3:00)
- **Tour Steps**: `Threat Matrix` → `Threat #1` → `Impact-based forecasting` → `Last-mile warning` → `12 Indian languages` → `Dispatch`
- **What to say**:
  > *"Raw rainfall numbers do not save lives—impact-based decision support does. Meghdrishti automatically clusters and ranks all heavy-rainfall zones according to IMD's standard thresholds: Yellow Watch, Orange Alert, and Red Warning (≥ 204.5 mm).*
  >
  > *By integrating Indian Census GIS population density grids, our system immediately computes the exact population exposed in the hazard zone and calculates a comprehensive Risk Index out of 100.*
  >
  > *For last-mile alerting, Meghdrishti autonomously drafts localized emergency advisories in 12 official Indian languages—complete with integrated text-to-speech audio for rural radio and cell broadcast."*

---

### Phase 5: Official MoES/IMD Civil Advisory & Conclusion (3:00 – 3:30)
- **Tour Steps**: `Official IMD Civil Bulletin` → `Meghdrishti Outro`
- **What to say**:
  > *"Finally, with a single click, Meghdrishti synthesizes the entire operational analysis into an official bilingual IMD Impact-Based Severe Weather Advisory Bulletin. It includes NDMA standard civil protection directives—advising District Magistrates on Emergency Operations Centre activation, NDRF pre-positioning, and hill route closures—and generates a print-ready, certified A4 civil report.*
  >
  > *Meghdrishti bridges raw atmospheric science, physics-informed deep learning, and last-mile civil protection—delivering an operational disaster decision support system for India. Thank you."*

---

## 3. High-Scoring Delivery Checklist
1. **Pacing**: Speak calmly and deliberately. Use the `Enter` key to synchronize transitions precisely with your words.
2. **Key Terms to Hit**:
   - *"NOAA GFS physics model & Copernicus ERA5 reanalysis"*
   - *"Indian bounding box: 8° to 38° North, 68° to 98° East"*
   - *"Custom Extreme-Weighted Loss function penalizing missed cloudbursts"*
   - *"FiLM lead-time conditioning"*
   - *"Per-pixel Explainable AI (XAI)"*
   - *"IMD impact-based warning tiers & Census GIS population exposure"*
   - *"NDMA Standard Operating Procedures"*
3. **Visual Highlights in Video**:
   - The animated swipe comparison between raw GFS and Super-UNet blend.
   - The interactive pixel inspector displaying the mathematical equation.
   - The audio playback of the regional language alert.
   - The official bilingual bulletin with State Emblem and single-page A4 print preview.
