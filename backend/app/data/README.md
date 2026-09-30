# Geospatial & Demographic Reference Data (Impact-Based Forecasting)

## Overview
This directory contains static geospatial and demographic reference data utilized by the **Impact-Based Forecasting (IBF)** engine (`backend/app/services/threat_detector.py`). 

Following World Meteorological Organization (WMO) and India Meteorological Department (IMD) guidelines for early warning systems, the Super-UNet pipeline pairs raw physical rainfall grids with demographic exposure layers to quantify civil risk before disaster onset.

---

## Datasets

### 1. `districts.json` (District Headquarters Gazetteer)
- **Source**: Survey of India & National Disaster Management Authority (NDMA) administrative boundaries.
- **Attributes**:
  - `district`: Official district administrative name.
  - `state`: Corresponding State / Union Territory of India.
  - `lat`, `lon`: Geographic coordinates (decimal degrees) of the district headquarters / Emergency Operations Centre (EOC).
- **Operational Purpose**:
  - **Hyper-Local Cluster Association**: Cross-references spatial contiguous rainfall clusters (IMD Heavy, Very Heavy, and Extremely Heavy) against the nearest district headquarters to generate localized warnings.
  - **Land-Sea Delineation**: Provides a mathematical land envelope (`LAND_RADIUS_KM = 70.0`) preventing maritime precipitation cells over the Arabian Sea / Bay of Bengal from triggering false inland alarms.

### 2. `state_density.json` (State Population Density Table)
- **Source**: Office of the Registrar General & Census Commissioner of India, Ministry of Home Affairs (Census of India).
- **Attributes**: Key-value mapping of State/UT names to population density (persons per square kilometer).
- **Operational Purpose**:
  - Used in conjunction with exact grid cell surface area (`_cell_area_km2()`) to calculate the number of individuals directly exposed (`population_exposed`) within severe weather zones.
  - Powers the composite **Risk Index (0–100)**:
    $$\text{Risk Index} = 100 \times \left(0.6 \times \min\left(\frac{\text{Peak Rainfall}}{1.5 \times 204.5\text{ mm}}, 1.0\right) + 0.4 \times \min\left(\frac{\log_{10}(\text{Exposed} + 1)}{7.0}, 1.0\right)\right)$$
