from typing import List, Optional, Dict

from bson import ObjectId
from pydantic import BaseModel, Field, conint, confloat
from models.user import PyObjectId  # Import custom ObjectId
from datetime import datetime
import pytz


# ---------------------------------------------------------------------
# --- Sub-Models for Verification Report (No Change) --------------------
# ---------------------------------------------------------------------

class MetricScore(BaseModel):
    """Standard structure for a single verification metric."""
    score: confloat(ge=0.0, le=1.0) = Field(..., description="Confidence score from 0.0 to 1.0.")
    details: str = Field(..., description="Detailed explanation of the check result.")


class PhotoMetadata(BaseModel):
    """Stores extracted EXIF and analysis data for one photo."""
    s3_key: str = Field(..., description="Key/Path to the stored file.")
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    capture_time: Optional[str] = None  # ISO format string


class ShadowAnalysisResult(MetricScore):
    """Result of the shadow analysis."""
    expected_sun_azimuth: Optional[float] = None
    expected_sun_elevation: Optional[float] = None
    detected_shadow_angle: Optional[float] = None


class SatelliteAnalysisResult(MetricScore):
    """Result of the satellite and YOLO analysis."""
    pre_install_panel_count: Optional[conint(ge=0)] = 0
    post_install_panel_count: Optional[conint(ge=0)] = 0
    yolo_confidence: Optional[float] = None


class EquipmentCheckResult(MetricScore):
    """Result of OCR and ALMM database check."""
    detected_serials: List[str] = Field(default_factory=list)
    verified_serials: List[str] = Field(default_factory=list)


class EnergyPrediction(BaseModel):
    """Expected vs Actual energy metrics."""
    expected_annual_kwh: Optional[float] = None
    actual_monthly_kwh: Optional[Dict[str, float]] = None  # For future monitoring


class VerificationReport(BaseModel):
    """The complete result and decision summary."""
    # Individual Checks
    gps_check: MetricScore
    shadow_analysis: ShadowAnalysisResult
    satellite_analysis: SatelliteAnalysisResult
    equipment_check: EquipmentCheckResult

    # Summary & Decision
    confidence_score: confloat(ge=0.0, le=1.0)
    decision: str = Field(..., description="Auto-approve, manual_review, or auto-reject.")
    reasoning: str = Field(..., description="Summary explanation of the final decision.")


# ---------------------------------------------------------------------
# --- Application Input Models (Step 1) --------------------------------
# ---------------------------------------------------------------------

class InitialApplicationCreate(BaseModel):
    """
    Input model for the detailed initial application before installation is verified.
    This model includes all the detailed customer and system information.
    """
    applicant_name: str = Field(..., description="Full name of the primary applicant.")
    applicant_phone: str = Field(..., description="Contact phone number of the applicant.")
    address: str = Field(..., description="Installation address.")
    system_capacity_kw: confloat(ge=0.1) = Field(..., description="Total system capacity in kW.")
    declared_panel_count: conint(ge=1) = Field(..., description="Number of solar panels to be installed.")
    installer_company: str = Field(..., description="Name of the installing company.")
    installer_contact: str = Field(..., description="Contact information for the installer.")
    preferred_verification_date: Optional[str] = Field(None, description="ISO date string for preferred verification.")


# ---------------------------------------------------------------------
# --- Main Application Data Model (Database Schema) ---------------------
# ---------------------------------------------------------------------

class ApplicationModel(BaseModel):
    """Model for a rooftop solar installation application in the database."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId

    # Installation Details (Expanded fields from InitialApplicationCreate)
    applicant_name: Optional[str] = None
    applicant_phone: Optional[str] = None
    address: str
    system_capacity_kw: float
    declared_panel_count: conint(ge=1)
    installer_company: Optional[str] = None
    installer_contact: Optional[str] = None
    preferred_verification_date: Optional[str] = None

    # Verification Details (Only filled after the verification step)
    registered_lat: Optional[float] = None
    registered_lon: Optional[float] = None
    wide_rooftop_photo: Optional[PhotoMetadata] = None
    serial_number_photo: Optional[PhotoMetadata] = None
    inverter_photo: Optional[PhotoMetadata] = None

    # Status and Verification
    status: str = Field("initial_application", description="e.g., initial_application, verifying, approved, rejected, manual_review")
    submission_date: str = Field(default_factory=lambda: str(datetime.now(pytz.timezone('Asia/Kolkata'))))

    # Report (only present after verification is complete)
    verification_report: Optional[VerificationReport] = None

    class Config:
        # Renamed in Pydantic V2 to validate_by_name, but kept for compatibility
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        # Allow extra fields temporarily if needed for future expansion
        extra = "allow"