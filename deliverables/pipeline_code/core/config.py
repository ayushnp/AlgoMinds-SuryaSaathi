# deliverables/pipeline_code/core/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# --- IMPORTANT: The parent of this file (core) is the base directory for imports ---
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Model configuration for loading .env file
    # NOTE: You must place your actual .env file in the root of the repository
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # --- External API Keys ---
    # These must be set in your .env file
    SENTINEL_HUB_CLIENT_ID: str = "3909a0cb-b588-48c6-955d-43ca7cbea633"
    SENTINEL_HUB_CLIENT_SECRET: str = "m2aDgwzNcigBAJ4oVHU7iRvfy0YfKXtt"


    # --- Storage Settings ---
    STORAGE_DIR: str = str(BASE_DIR / "storage")

    # --- Verification Weights (for Confidence Score) ---
    WEIGHT_GPS_MATCH: float = 0.30
    WEIGHT_SATELLITE_ANALYSIS: float = 0.30
    WEIGHT_EQUIPMENT_CHECK: float = 0.20
    WEIGHT_SHADOW_ANALYSIS: float = 0.20

    # --- Decision Engine Thresholds ---
    THRESHOLD_AUTO_APPROVE: float = 0.85
    THRESHOLD_MANUAL_REVIEW: float = 0.60


# Instantiate settings
settings = Settings()

# Ensure storage directory exists (for saving artefacts)
os.makedirs(settings.STORAGE_DIR, exist_ok=True)