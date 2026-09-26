# 0 - Project Setup

## Objective
Establish the monorepo architecture for the SIH26081 Forecast Blending System.

## Architecture
- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Vite
- **ML Pipeline**: PyTorch + Xarray
- **Data**: Stored locally in data/raw/ and data/processed/

## Implemented Components
- ackend/app/main.py: FastAPI entry point with CORS enabled.
- ackend/app/core/config.py: Environment configuration via Pydantic.
- rontend/: Initialized Vite React-TS boilerplate.

## Execution Commands
- **Run Backend**: cd backend && uvicorn app.main:app --reload
- **Run Frontend**: cd frontend && npm install && npm run dev
