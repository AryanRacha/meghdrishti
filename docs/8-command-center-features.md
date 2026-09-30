# 8 - Command Center Features (Phase 3D, video-ready)

## Objective
Make the dashboard tell the full story on screen: forecast, then explanation, then impact, then last-mile action.

## Features
| Feature | Where | Notes |
|---|---|---|
| Swipe compare (GFS vs Blend) | `components/map/SwipeCompare.tsx`, `SwipeDivider.tsx` | Two canvas heatmaps in separate Leaflet panes, clipped each side of a draggable divider (arrow keys supported). |
| Time-lapse playback | `App.tsx`, `ControlDock.tsx` (▶ next to date) | Advances one day per 1.4 s once the frame has rendered; prefetches the next day. `api/client.ts` keeps an LRU response cache (60 entries). |
| Impact / people at risk | backend `threat_detector.py`; `ThreatMatrix.tsx` | `population_exposed` and `risk_index` per threat (see doc 5). Shown in lakh/crore. |
| Multilingual public warning | `lib/alerts.ts`, `components/panels/AlertCard.tsx` | Fixed templates (no LLM, no network) in English, Hindi and the state language: Marathi, Bengali, Assamese, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Odia. |
| Voice read-out | `hooks/useSpeech.ts` | Browser `speechSynthesis`; prefers natural/online voices (Microsoft Edge ships Indian-language neural voices). Button disabled if the browser has no voice for that language. |
| Dispatch preview (mock) | `components/panels/DispatchPreview.tsx` | Phone mock-up plus channel list (Cell Broadcast, SMS, WhatsApp, District Control Room). Nothing is sent. |
| Guided Tour (~2 min) | `lib/storyScript.ts` (script), `hooks/useStoryMode.ts` (runner), `components/panels/StoryBar.tsx`, `StoryPanel.tsx` (full-screen explainer cards) | 19 steps in 3 acts: intro, problem, architecture and loss cards → GFS / AI / blend / swipe / Trust Map / variables / lead time / time-lapse → Threat Matrix, impact, spoken warning (first two sentences), languages, dispatch → outro. Starts on 27 Aug 2023. `Esc` stops. Edit durations in `storyScript.ts`. |
| Collapsible sidebars | `components/ui/EdgeToggle.tsx`, `App.tsx` | Controls (left) and Threat Matrix (right) slide in/out via edge tabs or `[` / `]`. The brand header always stays. During the tour each step declares `panels` (default: both hidden); controls show for lead-time and time-lapse, the Threat Matrix for the threat/impact steps. The user's layout is restored when the tour ends or on `Esc`. |

## Map Rendering
- `GET /api/v1/forecast/grid` returns the full 128×128 grid (~28 KB gzipped); the GeoJSON endpoint remains for external agencies.
- `lib/rasterize.ts` resamples the grid into Web Mercator pixels (1400 px wide), bilinearly interpolates values, **then** applies the colour scale, so IMD category contours stay crisp. Dry cells (< 1 mm) are transparent; edges are feathered (6 cells for rain, 14 for temperature/wind/trust).
- `components/map/RasterLayer.tsx` shows it as a Leaflet `ImageOverlay`, swapping frames only after the new image loads (no flicker during time-lapse); hover tooltips read the nearest cell.

## Rain Animation
- `components/map/RainAnimation.tsx`: screen-space rain streaks on a canvas above the map, shown only for the Rain variable (not Trust, not Compare).
- Drops spawn from a weighted table of 10 px screen cells with rain ≥ 2.5 mm; streak length, speed and brightness scale with intensity (log scale, saturating near 100 mm). Drops vanish when they leave the rain area.
- Batched into 4 stroke passes (one per brightness level), max 2,000 drops; hidden while the map pans or zooms and rebuilt afterwards. Disabled under `prefers-reduced-motion`.

## Recording Tips
- Use **Microsoft Edge** (for the neural Indian-language voices), 1920×1080, browser zoom 110–125%, hide the bookmarks bar.
- Click anywhere on the page once before starting the Guided Tour, so the browser allows audio.
- Wait for the first load; after that, toggles and playback frames come from the cache.
