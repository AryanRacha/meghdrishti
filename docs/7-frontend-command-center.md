# 7 - Frontend Command Center (Phase 3C)

## Objective
**Meghdrishti** (मेघदृष्टि, "cloud vision"): a single-screen React + Leaflet "command center" that renders the Super-UNet forecast over India and surfaces extreme-rain threats for forecasters (see `6-hackathon-presentation-and-usps.md`).

## Stack
React 19, TypeScript, Vite, TailwindCSS v4 (`@tailwindcss/vite`), Leaflet + react-leaflet 5. Esri Canvas Dark Gray basemap + reference labels (no API key; CARTO now watermarks keyless tiles).

## Layout
Full-screen map with floating glassmorphism panels:

| Panel | Position | Content |
|---|---|---|
| Header | top-left | Title + status badges (weights, data source, lead-time validity, loading) |
| Control Dock | left | Variable (Rain / Temp / Wind), Layer (GFS / AI / Blended / Trust), lead-time slider (24–120 h), date picker |
| Legend | bottom-left | Stepped IMD rain bins, or continuous gradient with min/max |
| Threat Matrix | right (bottom sheet on mobile) | Ranked IMD heavy-rain regions; click → map flies to the peak with a pulsing marker |

## Data Flow
1. `GET /api/v1/forecast/meta` on load → dates, lead times, trained lead times.
2. On any control change → `GET /api/v1/forecast/blended?...` (rain adds `min_value=1` to drop dry cells) and `GET /api/v1/forecast/alerts?...`.
3. Requests are aborted when superseded; previous data stays on screen while loading.
4. Vite dev server proxies `/api` and `/health` to `http://localhost:8000`.

## Rendering
- GeoJSON cells drawn imperatively with `L.geoJSON` on a shared **canvas renderer** (thousands of SVG paths would lag).
- Color scales (`src/lib/colorScales.ts`):
  - Rain: IMD 24 h bins; red is reserved for Extremely Heavy.
  - Temp: blue → yellow → red, 10–40 °C.
  - Wind: sequential teal → violet, 0–20 m/s.
  - Trust (XAI): diverging, violet = trust AI, teal = trust GFS.

## File Layout
```
frontend/src/
  App.tsx                         # state + composition
  types/forecast.ts               # API types (mirror backend/app/schemas)
  api/client.ts                   # URL builders + fetch
  hooks/useApi.ts                 # abortable fetch hook
  lib/colorScales.ts              # scales + legend stops
  lib/format.ts                   # labels / number formatting
  components/ui/GlassPanel.tsx    # shared glass container
  components/ui/Segmented.tsx     # segmented toggle
  components/map/ForecastMap.tsx  # map shell, basemap, bounds
  components/map/HeatmapLayer.tsx # canvas GeoJSON layer + hover tooltip
  components/map/ThreatMarkers.tsx# threat rings + selected pulse + flyTo
  components/panels/Header.tsx
  components/panels/ControlDock.tsx
  components/panels/Legend.tsx
  components/panels/ThreatMatrix.tsx
```

## Running
```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000
cd frontend && npm run dev   # http://localhost:5173
```

## Deferred (Phase 3D)
Swipe comparison slider, vulnerability/population overlay, GenAI briefing.
