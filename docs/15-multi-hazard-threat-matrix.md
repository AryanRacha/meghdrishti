# 15. Multi-Hazard Threat Matrix (Rain, Wind, Heat)

## Context & Objectives
The Threat Matrix, map markers, public warnings and bulletin only covered heavy rain. They now follow the selected variable (Rain / Temp / Wind), so the same impact-based workflow works for strong wind and heat.

---

## Detection Rules (`backend/app/services/threat_detector.py`)
Detection is table-driven: each hazard has a `HazardSpec` with units, a unit conversion, three ascending levels, a 0–1 intensity scale for the risk index, and a land-only flag.

| Hazard | Units | Level 1 | Level 2 | Level 3 | Land only |
|---|---|---|---|---|---|
| Rain | mm / 24 h | Heavy ≥ 64.5 | Very heavy ≥ 115.6 | Extremely heavy ≥ 204.5 | No (unchanged) |
| Wind | km/h | Strong wind ≥ 40 | Gale ≥ 62 | Storm-force ≥ 89 | Yes |
| Heat | °C | Heat watch (relative) | Heatwave ≥ 40 | Severe heatwave ≥ 45 | Yes |

- **Rain and wind** use IMD thresholds. Wind is converted from the model's m/s to km/h (IMD convention).
- **Heat watch is relative.** The temperature field is a single 2 m snapshot, not daily Tmax, so IMD heatwave thresholds almost never trigger, especially in monsoon months. The watch flags the **hottest 2% of land cells that day**, with a 28 °C floor so cool days raise nothing. The detection threshold is capped at 40 °C, so official heatwaves are always detected.
- **Land only**: wind and heat regions over the open sea are not public threats. Land is the existing exposure mask: within 70 km of a district HQ.
- **Risk index**: `60% × hazard intensity + 40% × log exposure`. Rain intensity is unchanged (`peak / (1.5 × 204.5)`). Wind spans 40 → 111 km/h; heat spans 28 → 47 °C.

## API (`GET /api/v1/forecast/alerts`)
- New query param `variable` (`rain` default | `temp` | `wind`).
- `Threat` schema changes:
  - Rain-specific fields renamed: `peak_mm → peak`, `mean_mm → mean`, `gfs_mm → gfs_value`, `ai_mm → ai_value`.
  - Added `variable`, `units`, and `level` (1–3).
  - `category` now spans all 9 hazard categories.
  - Threat ids include the variable.

## Frontend
- `lib/hazards.ts`: per-hazard UI text (matrix rule, empty state, bulletin title, level ranges, SOP directive).
- `lib/format.ts`: `CATEGORY_LABELS` for all 9 categories. Colours are keyed by **level** (`LEVEL_STYLES`, `LEVEL_COLORS`), so every hazard uses the same yellow / orange / red scale.
- `ThreatMatrix`, `ThreatMarkers`, `AlertCard`, `BulletinModal`: show `peak` with `units`, colour by `level`, and take hazard text from `HAZARDS[variable]`.
- `App.tsx`: alerts are fetched (and prefetched during playback) for the selected variable.
- `lib/alerts.ts`: each language pack has `body.rain`, `body.wind` and `body.temp` templates and labels for all 9 categories. Rain text is unchanged.
  - In Assamese, Punjabi and Odia, clock times in heat warnings are written as words, because their MMS speech models cannot read digits.
- `backend/app/services/tts_engine.py`: MMS normalisation also expands `km` and `°C` for Assamese, Punjabi and Odia.

## Tests
- `tests/test_threat_detector.py`: grading for each hazard.
- `tests/test_api.py::test_wind_and_heat_alerts`: units, categories, levels and ranking for wind and heat.
