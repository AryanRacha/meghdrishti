# 13. Map Elevation & Cartographic Polish

## Context & Objectives
To differentiate Meghdrishti from generic web map dashboards and ensure clear visual contrast during live demos and video presentations:
1. **Remove Rain Animation Clutter**: The falling diagonal rain streaks cluttered the visual field and obscured regional borders.
2. **Rain Scale Contrast**: Pale cyan/white hues previously blended into the basemap and national border. Replaced with high-contrast radar hues and calibrated atmospheric alpha.
3. **Elevated Subcontinent Relief Effect**: Spotlight the Indian subcontinent so it appears elevated as a 3D relief plate above neighboring regions and the Indian Ocean.

---

## Technical Implementation

### 1. Inverted Dimming Mask (`frontend/src/data/india-mask.json`)
- Built an inverted world polygon covering `[-180, -85]` to `[180, 85]` with India's official Survey of India composite polygon (mainland + 53 offshore island polygons) punched out as inner holes.
- Mounted in Leaflet under `<Pane name="india-focus-mask" style={{ zIndex: 440 }}>`:
  - `fillColor: '#020617'`
  - `fillOpacity: 0.38`
- Non-Indian landmasses and surrounding seas are subtly darkened, while all meteorological features and geography inside India remain 100% luminous.

### 2. Physical 3D Elevation & Drop Shadow (`ForecastMap.tsx`)
- Configured `<Pane name="india-border" style={{ zIndex: 460 }}>` with dual physical drop-shadow filters:
  - `drop-shadow(0 2px 4px rgba(0, 0, 0, 0.95))` (sharp ground occlusion)
  - `drop-shadow(0 6px 14px rgba(0, 0, 0, 0.85))` (ambient elevation blur)
- Rendered official SoI boundary with a two-pass stroke system:
  1. **Halo Backing**: `#000000` at `weight: 4.5`, `opacity: 0.85`.
  2. **Elevated Border**: `#f8fafc` (crisp platinum) at `weight: 1.8`, `opacity: 0.95`.
- Ensures 100% border legibility even over torrential radar cores (red/amber rain cells).

### 3. Vibrant Rain Scale & Calibrated Alpha Curve (`colorScales.ts`)
- Replaced muddy/dimmed hues with vibrant, luminous radar blues and alert tones:
  - $\ge 1.0\text{ mm}$: `#38bdf8` (vivid sky cyan, $\alpha = 0.45$)
  - $\ge 2.5\text{ mm}$: `#0ea5e9` (electric sky blue, $\alpha = 0.55$)
  - $\ge 15.6\text{ mm}$: `#2563eb` (royal blue, $\alpha = 0.73$)
  - $\ge 64.5\text{ mm}$: `#facc15` (bright gold/amber, $\alpha = 0.78$)
  - $\ge 115.6\text{ mm}$: `#f97316` (vivid orange, $\alpha = 0.88$)
  - $\ge 204.5\text{ mm}$: `#ef4444` (crimson red, $\alpha = 0.88$)
- Smooth atmospheric feathering keeps coastlines, terrain, and city labels crisp while ensuring rain bands across the country are vibrant and immediately legible.

### 4. Clean Streamlined Canvas (`App.tsx`)
- Removed `RainAnimation` component to eliminate visual artifacts and preserve frame rates during high-resolution screen recordings.

### 5. Unified Bottom Workspace & Threat Matrix Synchronization
- **Shared Flex Container**: Coordinated `AlertCard` (Public Warning) and `PixelInspector` (XAI Inspector) inside a single dynamic bottom flex container (`items-end justify-center gap-3.5`). Eliminates collision and overlapping when both cards are active.
- **Threat-to-Inspector Linkage**: Updated `selectThreat` in `App.tsx` so selecting an event from the Threat Matrix (or a map marker) automatically populates `inspectPoint` with the threat's exact coordinates (`lat`, `lon`), pulling up the XAI model decomposition side-by-side with the multilingual advisory.
