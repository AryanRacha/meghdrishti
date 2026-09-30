import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.forecast import router as forecast_router
from app.core.config import settings
from app.schemas.forecast import HealthResponse
from app.services.inference_engine import InferenceEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    InferenceEngine.get()  # load weights once at startup
    yield


app = FastAPI(title="SIH26081 Weather Blending API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(forecast_router, prefix=settings.API_V1_STR)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    engine = InferenceEngine.get()
    return HealthResponse(
        status="ok",
        model_loaded=True,
        weights=engine.weights_mode,
        device=str(engine.device),
    )


def dev() -> None:
    """Run local development server with auto-reload."""
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


def start() -> None:
    """Run production server."""
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, workers=2)


if __name__ == "__main__":
    dev()

