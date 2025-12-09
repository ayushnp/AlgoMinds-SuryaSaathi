# deliverables/pipeline_code/models/application.py
from pydantic import BaseModel, Field
from typing import Optional


# --- ENUM for QC Status (Mandatory Output) ---
class QCStatus:
    VERIFIABLE = "VERIFIABLE"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"


# --- Metric Scores (General) ---
class MetricScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    details: Optional[str] = None


# --- Satellite Analysis Specific Result (Core Objective Output) ---
class SatelliteAnalysisResult(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    details: str

    # Quantification and Detection Results
    pre_install_panel_count: int
    post_install_panel_count: int
    pv_area_sqm_est: float = Field(..., description="Estimated total PV area in square meters (m²)")
    yolo_confidence: float = Field(..., ge=0.0, le=1.0)

    # Explainability/Auditability
    qc_status: str = Field(..., description="VERIFIABLE or NOT_VERIFIABLE")
    image_metadata: dict = Field(default_factory=dict)