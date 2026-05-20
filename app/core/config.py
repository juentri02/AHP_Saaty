# app/core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load the .env file automatically
load_dotenv()

class Settings:
    APP_NAME = os.getenv("APP_NAME", "AHP Profiler")
    
    # Root directory is two levels up from this file
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    # Paths
    DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
    LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")
    
    # AHP Rules
    CR_TOLERANCE = float(os.getenv("CONSISTENCY_TOLERANCE", 0.1))

settings = Settings()