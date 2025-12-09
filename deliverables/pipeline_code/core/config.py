import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Determine the base directory for relative path resolution
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Model configuration for loading .env file
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # --- Application Settings ---
    PROJECT_NAME: str = "Surya Saathi Verification API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # --- MongoDB Settings ---
    MONGO_DB_URI: str
    MONGO_DB_NAME: str = "surya_saathi_db"

    # --- JWT Security Settings ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours for a mobile app session

    # --- External API Keys ---
    SENTINEL_HUB_CLIENT_ID: str
    SENTINEL_HUB_CLIENT_SECRET: str
    NREL_PVWATTS_API_KEY: str

    # --- Storage Settings ---
    # Using local path for simplicity, replace with S3 bucket details for production
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

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)