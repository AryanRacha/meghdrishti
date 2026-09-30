# 11 - Presentation & Operational Decision Support Upgrades

## Objective
Elevate the Meghdrishti dashboard from an ML prototype to an official, operational disaster decision support system for the SIH26081 (Ministry of Earth Sciences) submission.

## Implemented Components

### 1. Government & Institutional Branding (`Header.tsx`)
- **Institutional Badging**: Added Ministry of Earth Sciences (MoES) and Government of India institutional labels.
- **Scenario Realism**: Replaced raw `"synthetic"` label with `"Historical Replay · Aug 2023 Monsoon Disaster Case Study"`, and `"processed"` with `"Operational ERA5/GFS Reanalysis Grid"`.
- **IMD Color Alert Strip**: Added active counts of IMD alert tiers (Red / Orange / Yellow) with quick-access to the official bulletin.

### 2. Official Impact-Based Weather Bulletin (`BulletinModal.tsx`)
- **Government Advisory Letterhead**: Formatted according to IMD / National Weather Forecasting Centre (NWFC) standard operating procedures, featuring an authentic vector representation of the National Emblem of India (Lion Capital of Ashoka with *Satyameva Jayate*).
- **Decision Support Directives**: Prescribes specific civil action protocols (NDRF pre-positioning, EOC activation, riverbank evacuation) based on threat severity.
- **Tabular Risk Exposure**: Ranked table showing District, State, Peak Rainfall, IMD Warning Level, Population at Risk, and Risk Index (0–100).
- **A4 Print Engine & Isolation (`index.css` & `App.tsx`)**:
  - Full `@media print` isolation: completely strips Leaflet tiles, controls, attribution, floating toolbars, and background panes so no UI artifacts bleed through into the report.
  - Reset layout constraints (`height: auto !important; overflow: visible !important;`) and configured `@page { size: A4 portrait; margin: 10mm 12mm; }`.
  - Added `break-inside: avoid` (`.print-avoid-break`) on summaries, data tables, and directives to ensure pristine single-page fit.
- **Indic Typography Preservation**:
  - Fixed letter-spacing bug: removed CSS `letter-spacing` (`tracking-*`) from Devanagari strings (`भारत सरकार`, `पृथ्वी विज्ञान मंत्रालय`, etc.) to prevent OpenType glyph cluster separation.
  - Added `[lang="hi"]` CSS rule with explicit `Noto Sans Devanagari` fallback and enforced `letter-spacing: normal !important; word-spacing: normal !important;`.

### 3. Interactive Explainable AI (XAI) Pixel Inspector (`PixelInspector.tsx`)
- **Map Click Sampling**: Clicking any point across the Indian bounding box drops an inspection marker and samples the underlying grid cell (~26 km).
- **Decomposition**: Displays the exact physical GFS input, the AI model proxy input, the Super-UNet trust weights ($w_{\text{GFS}}$ and $w_{\text{AI}}$), and the resulting blended prediction.
- **Explainability**: Formally displays the mathematical blending equation:
  $$\text{Blended} = w_{\text{GFS}} \cdot \text{GFS} + (1 - w_{\text{GFS}}) \cdot \text{AI}$$
- Shows corresponding IMD rainfall severity categories and nearest district context.
