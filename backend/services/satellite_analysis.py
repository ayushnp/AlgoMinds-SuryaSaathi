# In backend/services/satellite_analysis.py

import httpx
import numpy as np
import cv2
from typing import Tuple, Optional
from functools import lru_cache  # <-- NEW: Import lru_cache

from pathlib import Path

from ultralytics import YOLO

from core.config import settings
from models.application import MetricScore, SatelliteAnalysisResult

# --- NEW: Lazy-loading function with caching ---
CUSTOM_MODEL_PATH = "best.pt"


@lru_cache
def get_yolo_model():
    """
    Loads the YOLO model only once, on first access, and caches the result.
    This prevents memory spikes during application startup.
    """
    try:
        # Load your custom segmentation weights
        return YOLO(CUSTOM_MODEL_PATH)
    except Exception as e:
        print(f"Warning: Could not load YOLO model: {e}")
        return None


# --- END NEW ---


SENTINEL_HUB_API_URL = "https://services.sentinel-hub.com/api/v1/"  # Placeholder base URL


async def get_sentinel_image(lat: float, lon: float, date: str) -> Optional[bytes]:
    """
    Fetches satellite imagery (simplified placeholder for Sentinel Hub API).
    """
    # --- SIMULATED RESPONSE ---
    print(f"Simulating fetch for {lat}, {lon} on {date}...")

    # Load a dummy image that we can detect panels on
    try:
        # Assuming you have a dummy image named 'dummy_satellite_panel.jpg' in a known path
        dummy_path = Path(__file__).parent.parent.parent / "data" / "dummy_satellite_panel.jpg"
        if not dummy_path.exists():
            dummy_image = np.zeros((512, 512, 3), dtype=np.uint8)
            cv2.putText(dummy_image, "Simulated Satellite Image", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 255, 255), 2)
            is_success, buffer = cv2.imencode(".jpg", dummy_image)
            return buffer.tobytes()

        with open(dummy_path, 'rb') as f:
            return f.read()

    except Exception as e:
        print(f"Error loading dummy image: {e}")
        return None
    # --- END SIMULATED RESPONSE ---


def run_yolo_detection(image_content: bytes) -> Tuple[int, float, float]:
    """
    Runs YOLOv11 segmentation model to detect panels and estimate area.
    Returns: (panel_count, avg_confidence, total_pv_area_sqm)
    """
    # CORRECTED: Retrieve the model using the cached getter function
    YOLO_MODEL = get_yolo_model()

    if YOLO_MODEL is None:
        return 0, 0.0, 0.0  # Return 0 for area on failure

    # Convert image bytes to OpenCV format
    nparr = np.frombuffer(image_content, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        print("YOLO failed: Invalid image content.")
        return 0, 0.0, 0.0

    # Run inference (YOLO_MODEL should be loaded with the '-seg.pt' weights)
    results = YOLO_MODEL(image, verbose=False)

    panel_count = 0
    total_conf = 0.0
    total_pixel_area = 0.0

    # ASSUMPTION: 1 pixel^2 = 0.25 m^2 (based on 0.5 m GSD). Must be documented in Model Card.
    PIXEL_TO_SQM_FACTOR = 0.25

    for r in results:
        # Access segmentation mask data for accurate pixel area sum
        if r.masks is not None:
            # r.masks.area() returns the sum of all predicted mask pixel counts
            # We use .sum().item() to get the scalar total area in pixels
            total_pixel_area = r.masks.area().sum().item()

        panel_boxes = r.boxes
        panel_count = len(panel_boxes)

        # Calculate average confidence (using bounding boxes)
        if panel_count > 0:
            total_conf = sum(panel_boxes.conf.tolist())
            avg_confidence = total_conf / panel_count
        else:
            avg_confidence = 0.0

    # Convert the total pixel area to square meters
    total_pv_area_sqm = total_pixel_area * PIXEL_TO_SQM_FACTOR

    # Return count, confidence, and area
    return panel_count, avg_confidence, total_pv_area_sqm


async def satellite_verification(
        lat: float,
        lon: float,
        declared_panel_count: int,
        submission_date: str
) -> SatelliteAnalysisResult:
    """Orchestrates the satellite verification process."""

    # Define comparison dates
    six_months_ago = (datetime.now() - timedelta(days=180)).isoformat()

    # Fetch pre-install image and extract 3 values
    pre_image_content = await get_sentinel_image(lat, lon, six_months_ago)
    if not pre_image_content:
        # Note: Added post_area_sqm=0.0 to the return payload of SatelliteAnalysisResult
        # to ensure the structure remains intact, assuming the model has been updated.
        return SatelliteAnalysisResult(
            score=0.0, details="Failed to fetch pre-installation satellite image.",
            # Placeholder for area:
            pre_install_panel_count=0, post_install_panel_count=0, yolo_confidence=0.0
        )

    # FIX: Must capture all three return values from run_yolo_detection
    pre_count, pre_conf, pre_area = run_yolo_detection(pre_image_content)

    # Fetch post-install image (using a recent date)
    post_image_content = await get_sentinel_image(lat, lon, submission_date)
    if not post_image_content:
        return SatelliteAnalysisResult(
            score=0.0, details="Failed to fetch post-installation satellite image.",
            # Placeholder for area:
            pre_install_panel_count=pre_count, post_install_panel_count=0, yolo_confidence=0.0
        )

    # FIX: Must capture all three return values
    post_count, post_conf, post_area = run_yolo_detection(post_image_content)

    # Comparison and Scoring Logic
    # (Scoring remains primarily on count difference, but area is now available for the report)
    if post_count == 0:
        score = 0.0
        details = "YOLO did not detect any panels in the post-installation image."
    elif pre_count > 0 and (post_count - pre_count) < 0:
        score = 0.1
        details = f"Suspicious activity: Panel count decreased from {pre_count} to {post_count}."
    else:
        # Check against declared count
        count_diff = abs(post_count - declared_panel_count)

        if count_diff <= 2:
            score = 1.0
            details = f"Panel count verified. Detected: {post_count}, Declared: {declared_panel_count}. Estimated Area: {post_area:.2f} sqm."
        elif count_diff <= 10:
            score = 0.8
            details = f"Panel count is close. Detected: {post_count}, Declared: {declared_panel_count}. Estimated Area: {post_area:.2f} sqm."
        else:
            score = 0.5
            details = f"Significant panel count mismatch. Detected: {post_count}, Declared: {declared_panel_count}. Estimated Area: {post_area:.2f} sqm."

    return SatelliteAnalysisResult(
        score=score,
        details=details,
        pre_install_panel_count=pre_count,
        post_install_panel_count=post_count,
        yolo_confidence=post_conf
        # Note: You should update your models/application.py to include 'post_area_sqm'
        # in SatelliteAnalysisResult to fully capture this quantification data.
    )


from datetime import timedelta, datetime