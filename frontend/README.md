# Meghdrishti Frontend (React + TypeScript + Vite + Bun)

Command center for the SIH26081 Hybrid AI-NWP Super-Ensemble Blending System.

## Development with Bun

```bash
# Install dependencies
bun install

# Start local dev server (http://localhost:5173)
bun run dev

# Build for production
bun run build

# Run Oxlint
bun run lint
```

## Features
- Interactive Leaflet map with smooth Mercator raster layers (Rainfall, Temperature, Wind, XAI Trust).
- IMD heavy rainfall alerts and Threat Matrix ranking.
- Swipe comparison between raw GFS and blended forecast.
- Multilingual automated disaster warnings with speech synthesis.
- Guided Tour walkthrough mode.
