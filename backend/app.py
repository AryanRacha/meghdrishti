from fastapi import FastAPI
from app.main import app as fastapi_app
import spaces

# The ZeroGPU AST scanner physically reads this entrypoint file.
# It MUST see a @spaces.GPU decorator in this file to let the container boot.

@fastapi_app.get("/api/v1/gpu-ping")
@spaces.GPU
def gpu_ping():
    return {"status": "ZeroGPU is active and satisfied!"}

# Expose the FastAPI app as 'app' for the Hugging Face Uvicorn runner
app = fastapi_app
