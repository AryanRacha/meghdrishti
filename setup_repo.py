import os

base_dir = r'C:\Users\student\coding\sih-project'
os.makedirs(base_dir, exist_ok=True)

# 1. Root Files
with open(os.path.join(base_dir, '.gitignore'), 'w', encoding='utf-8') as f:
    f.write('node_modules/\n__pycache__/\n*.pyc\n.env\nvenv/\n.venv/\ndata/raw/\ndata/processed/\n')

with open(os.path.join(base_dir, 'README.md'), 'w', encoding='utf-8') as f:
    f.write('# SIH26081: Hybrid AI-NWP Forecast Blending System\n\nMonorepo containing Frontend, Backend, and ML Pipeline.\n')

# 2. Backend Structure
backend_dir = os.path.join(base_dir, 'backend')
os.makedirs(os.path.join(backend_dir, 'app', 'api'), exist_ok=True)
os.makedirs(os.path.join(backend_dir, 'app', 'core'), exist_ok=True)
os.makedirs(os.path.join(backend_dir, 'app', 'services'), exist_ok=True)

with open(os.path.join(backend_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
    f.write('fastapi\nuvicorn\npydantic\npydantic-settings\nxarray\nnetCDF4\n')

main_py_code = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SIH26081 Weather Blending API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running optimally."}
"""
with open(os.path.join(backend_dir, 'app', 'main.py'), 'w', encoding='utf-8') as f:
    f.write(main_py_code)

config_py_code = """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26081 Weather API"
    API_V1_STR: str = "/api/v1"
    
    class Config:
        case_sensitive = True

settings = Settings()
"""
with open(os.path.join(backend_dir, 'app', 'core', 'config.py'), 'w', encoding='utf-8') as f:
    f.write(config_py_code)

# 3. ML Pipeline Structure
ml_dir = os.path.join(base_dir, 'ml_pipeline')
os.makedirs(os.path.join(ml_dir, 'data_fetchers'), exist_ok=True)
os.makedirs(os.path.join(ml_dir, 'utils'), exist_ok=True)
os.makedirs(os.path.join(base_dir, 'data', 'raw'), exist_ok=True)
os.makedirs(os.path.join(base_dir, 'data', 'processed'), exist_ok=True)

with open(os.path.join(ml_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
    f.write('xarray\nnetCDF4\ncfgrib\ncdsapi\nrequests\npandas\nboto3\nscipy\n')

with open(os.path.join(ml_dir, 'data_fetchers', '__init__.py'), 'w', encoding='utf-8') as f:
    f.write('')
with open(os.path.join(ml_dir, 'utils', '__init__.py'), 'w', encoding='utf-8') as f:
    f.write('')

print("Python setup completed successfully.")
