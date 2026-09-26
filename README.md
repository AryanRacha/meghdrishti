# SIH26081: Hybrid AI-NWP Forecast Blending System

This repository contains the solution for SIH26081 (Ministry of Earth Sciences). It blends physical NWP forecasts (GFS) with AI models using a PyTorch Spatial U-Net to predict highly accurate weather outcomes while explicitly preserving extreme weather events (cloudbursts).

## Directory Structure
- docs/ - Architectural decisions and implementation steps.
- AGENTS.md - Core instructions for AI Agents working on this repo.
- ackend/ - FastAPI server.
- rontend/ - React + TypeScript UI Dashboard (Vite).
- ml_pipeline/ - PyTorch U-Net, Data Fetchers, and Training loops.

## Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Copernicus CDS API Key** (Required for ERA5 ground truth data)

---

## Getting Started

### 1. ML Pipeline & Data (Python)
`ash
cd ml_pipeline
pip install -r requirements.txt
`
*Note: To download ERA5 data, ensure your API key is placed in ~/.cdsapirc.*
Run the training loop (mock data fallback is enabled if raw data is missing):
`ash
python train.py
`

### 2. Backend (FastAPI)
`ash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
`
API runs on http://127.0.0.1:8000. Swagger UI at /docs.

### 3. Frontend (React)
`ash
cd frontend
npm install
npm run dev
`
Dashboard runs on http://localhost:5173.
