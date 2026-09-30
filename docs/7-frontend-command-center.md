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
2. On any control change → `GET /api/v1/forecast/grid?...` and `GET /api/v1/forecast/alerts?...`.
3. Superseded responses are ignored; previous data stays on screen while loading. `api/client.ts` keeps an LRU cache (60 responses) so toggles and playback frames are instant after first load.
4. Vite dev server proxies `/api` and `/health` to `http://localhost:8000`.

## Rendering
- The grid is rasterised in the browser (`lib/rasterize.ts`): resampled to Web Mercator (1400 px wide), bilinearly interpolated, **then** coloured, so IMD category contours stay crisp. Dry cells (< 1 mm) are transparent and the grid edges are feathered. Shown as a Leaflet `ImageOverlay` (`RasterLayer.tsx`).
- Rain gets an animated streak overlay (`RainAnimation.tsx`). Details in `8-command-center-features.md`.
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
  hooks/useApi.ts                 # fetch hook (ignores superseded responses)
  hooks/useSpeech.ts              # speechSynthesis wrapper
  hooks/useStoryMode.ts           # Guided Tour runner
  lib/colorScales.ts              # RGB scales + legend stops
  lib/rasterize.ts                # grid -> smooth Mercator PNG
  lib/alerts.ts                   # multilingual warning templates
  lib/storyScript.ts              # Guided Tour steps
  lib/format.ts                   # labels / number formatting
  components/ui/GlassPanel.tsx    # shared glass container
  components/ui/Segmented.tsx     # segmented toggle
  components/ui/EdgeToggle.tsx    # sidebar show/hide tab
  components/map/ForecastMap.tsx  # map shell, basemap, bounds
  components/map/RasterLayer.tsx  # smooth raster overlay + hover tooltip
  components/map/RainAnimation.tsx# rain streak canvas
  components/map/SwipeCompare.tsx # GFS vs blend clipped panes
  components/map/SwipeDivider.tsx # draggable divider
  components/map/MapController.tsx# reset-view fly-to
  components/map/ThreatMarkers.tsx# threat rings + selected pulse + flyTo
  components/panels/Header.tsx
  components/panels/ControlDock.tsx
  components/panels/Legend.tsx
  components/panels/ThreatMatrix.tsx
  components/panels/AlertCard.tsx
  components/panels/DispatchPreview.tsx
  components/panels/StoryBar.tsx
  components/panels/StoryPanel.tsx
```

## Running
```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000
cd frontend && npm run dev   # http://localhost:5173
```

## Phase 3D
Swipe compare, time-lapse, impact estimates, multilingual voice warnings, dispatch preview, Guided Tour, rain animation and collapsible sidebars are built. See `8-command-center-features.md`. Still deferred: GenAI (LLM) briefing.
