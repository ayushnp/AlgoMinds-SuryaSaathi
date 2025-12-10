# deliverables/pipeline_code/services/satellite_analysis.py

import numpy as np
import cv2
from typing import Tuple, Optional, Dict
from functools import lru_cache
from pathlib import Path
from datetime import timedelta, datetime

# --- SENTINEL HUB IMPORTS ---
from sentinelhub import (
    SentinelHubSession, BBox, CRS, DataCollection, MimeType,
    SHConfig, SentinelHubRequest, get_area_geom
)
from shapely.geometry import Point
# --- END SENTINEL HUB IMPORTS ---

# Relative imports from the pipeline structure
from core.config import settings
from models.application import SatelliteAnalysisResult, QCStatus

# --- SENTINEL HUB CONSTANTS ---
DATA_COLLECTION = DataCollection.SENTINEL2_L2A
IMAGE_RESOLUTION_M = 10  # Sentinel-2 L2A is 10 meters per pixel for RGB/NIR bands
MAX_CLOUD_COVERAGE = 20

# Buffer zone conversion (Core Objective 2)
SQFT_TO_M2 = 0.092903
# Radius is calculated from Area = pi * r^2 --> r = sqrt(Area / pi)
TARGET_RADII_M = {
    1200: (1200 * SQFT_TO_M2 / np.pi) ** 0.5,  # ~5.95 meters
    2400: (2400 * SQFT_TO_M2 / np.pi) ** 0.5  # ~8.42 meters
}


# --- END SENTINEL HUB CONSTANTS ---


# --- 1. AUTHENTICATION & SESSION MANAGEMENT ---
@lru_cache
def get_sh_session() -> SentinelHubSession:
    """
    Creates and caches the Sentinel Hub session.
    """
    config = SHConfig()
    config.sh_client_id = settings.SENTINEL_HUB_CLIENT_ID
    config.sh_client_secret = settings.SENTEL_HUB_CLIENT_SECRET

    if not config.sh_client_id or not config.sh_client_secret:
        raise ValueError("Sentinel Hub credentials are not configured.")

    try:
        return SentinelHubSession(config=config)
    except Exception as e:
        print(f"Error during Sentinel Hub authentication: {e}")
        raise


# --- 2. GEOMETRY UTILITY ---
def get_bbox_from_point(lat: float, lon: float, buffer_radius_sqft: int) -> BBox:
    """
    Calculates a small BBox that encompasses the required circular buffer.
    """
    radius_m = TARGET_RADII_M.get(buffer_radius_sqft, TARGET_RADII_M[2400])

    # Use WGS84 to define the point, then project to get the buffer.
    # We use a simple degree approximation for the small buffer's extent.

    # Approximate degree change for the radius (simplified for small areas)
    lat_rad = np.radians(lat)
    delta_lon = radius_m / (111320 * np.cos(lat_rad))
    delta_lat = radius_m / 110540

    bbox_coords = [
        lon - delta_lon, lat - delta_lat,
        lon + delta_lon, lat + delta_lat
    ]

    return BBox(bbox=bbox_coords, crs=CRS.WGS84)


# --- 3. CORE EVALSCRIPT (The Math in the Cloud) ---
EVALSCRIPT_TRUE_COLOR_RGB_JPEG = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B02", "B03", "B04", "dataMask"],
      units: "DN"
    }],
    output: {
      id: "default",
      bands: 3,
      sampleType: "UINT8"
    }
  };
}

function evaluatePixel(sample) {
  // Simple contrast stretching (factor of 3.5 works well for Sentinel-2)
  let factor = 3.5;
  let r = sample.B04 * factor;
  let g = sample.B03 * factor;
  let b = sample.B02 * factor;

  // Cloud filtering: if dataMask is 0, the pixel is invalid.
  if (sample.dataMask === 0) {
    return [0, 0, 0]; // Return black for invalid pixels
  }

  // Return the RGB bands, clipped to 0-255 range for UINT8 output
  return [r, g, b];
}
"""

# --- 4. YOLO MODEL LOADING ---
CUSTOM_MODEL_PATH = Path(__file__).parent.parent.parent / "trained_model_file" / "best.pt"


@lru_cache
def get_yolo_model():
    """Loads the YOLO model only once, on first access, and caches the result."""
    from ultralytics import YOLO  # Assumes ultralytics is installed
    try:
        # Load your custom segmentation weights
        return YOLO(str(CUSTOM_MODEL_PATH))
    except Exception as e:
        print(f"Warning: Could not load YOLO model at {CUSTOM_MODEL_PATH}: {e}")
        return None


# --- 5. IMAGE FETCHING ---

def fetch_sh_image(
        lat: float,
        lon: float,
        time_interval: Tuple[str, str],
        buffer_radius_sqft: int,
) -> Tuple[Optional[bytes], Dict[str, str]]:
    """
    Fetches the best available Sentinel Hub image and metadata.
    """
    session = None
    try:
        session = get_sh_session()
        bbox = get_bbox_from_point(lat, lon, buffer_radius_sqft)

        # Determine the size in pixels, ensuring a minimum size for the API
        size_x = int(bbox.get_width() / IMAGE_RESOLUTION_M)
        size_y = int(bbox.get_height() / IMAGE_RESOLUTION_M)
        size = [max(size_x, 100), max(size_y, 100)]

        request = SentinelHubRequest(
            session=session,
            evalscript=EVALSCRIPT_TRUE_COLOR_RGB_JPEG,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DATA_COLLECTION,
                    time_interval=time_interval,
                    maxcc=MAX_CLOUD_COVERAGE,
                    mosaicking_order='leastCC'  # Select the least cloudy scene
                )
            ],
            responses=[
                SentinelHubRequest.output_response("default", MimeType.JPEG),
                SentinelHubRequest.output_response("userdata", MimeType.JSON)  # Get metadata
            ],
            bbox=bbox,
            size=size
        )

        data = request.get_data()

        if data and len(data) == 2:
            image_content = data[0]
            metadata = data[1]['userdata']  # Extracting the metadata response

            # Extract sensing time from metadata for auditability
            sensing_time = metadata.get('tileDate', 'N/A')

            return image_content, {"source": DATA_COLLECTION.name, "capture_date": sensing_time}

        return None, {}

    except Exception as e:
        # Check if the error is a '400 Bad Request' which often means no data found
        print(f"Sentinel Hub API Error for {lat}, {lon}: {e}")
        return None, {}


# --- 6. YOLO DETECTION AND QUANTIFICATION ---
def run_yolo_detection(image_content: bytes) -> Tuple[int, float, float, Optional[bytes]]:
    """
    Runs YOLO segmentation, estimates area, and returns overlay image.
    Returns: (panel_count, avg_confidence, total_pv_area_sqm, overlay_image_bytes)
    """
    YOLO_MODEL = get_yolo_model()
    if YOLO_MODEL is None:
        return 0, 0.0, 0.0, None

    nparr = np.frombuffer(image_content, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        return 0, 0.0, 0.0, None

    # Run inference
    results = YOLO_MODEL(image, verbose=False)

    panel_count = 0
    total_conf = 0.0
    total_pixel_area = 0.0
    overlay_image_bytes = None

    # Factor based on the Sentinel-2 10m resolution (10m * 10m = 100 sqm/pixel)
    PIXEL_TO_SQM_FACTOR = IMAGE_RESOLUTION_M * IMAGE_RESOLUTION_M

    for r in results:
        if r.masks is not None:
            total_pixel_area = r.masks.area().sum().item()

        panel_boxes = r.boxes
        panel_count = len(panel_boxes)

        if panel_count > 0:
            total_conf = sum(panel_boxes.conf.tolist())
            avg_confidence = total_conf / panel_count
        else:
            avg_confidence = 0.0

        # Create the audit artifact (overlay image)
        im_with_boxes = r.plot()
        is_success, buffer = cv2.imencode(".jpg", im_with_boxes)
        if is_success:
            overlay_image_bytes = buffer.tobytes()

    total_pv_area_sqm = total_pixel_area * PIXEL_TO_SQM_FACTOR

    return panel_count, avg_confidence, total_pv_area_sqm, overlay_image_bytes


# --- 7. MAIN ORCHESTRATOR ---
async def satellite_verification(
        lat: float,
        lon: float,
        declared_panel_count: int,
        submission_date: str,
        sample_id: str
) -> SatelliteAnalysisResult:
    """
    Orchestrates the complete satellite verification process and generates artifacts.
    """

    submission_dt = datetime.fromisoformat(submission_date.split('T')[0])

    # 7.1 Define Time Ranges
    # Pre-install: Look 6 months prior to submission date
    six_months_ago = (submission_dt - timedelta(days=180)).isoformat().split('T')[0]
    pre_install_period = (six_months_ago, submission_date)

    # Post-install: Look from submission date up to now
    post_install_period = (submission_date, datetime.now().isoformat().split('T')[0])

    # 7.2 Fetch Pre-install Image (2400 sq ft buffer)
    pre_content, pre_metadata = fetch_sh_image(lat, lon, pre_install_period, 2400)

    # 7.3 Handle Image Fetch Failure
    if pre_content is None:
        return SatelliteAnalysisResult(
            score=0.0, details="Pre-installation image fetch failed. Likely heavy cloud cover or no data.",
            pre_install_panel_count=0, post_install_panel_count=0, yolo_confidence=0.0,
            pv_area_sqm_est=0.0, qc_status=QCStatus.NOT_VERIFIABLE, image_metadata={}
        )

    # 7.4 Run YOLO on Pre-install Image
    pre_count, _, _, _ = run_yolo_detection(pre_content)

    # 7.5 Fetch Post-install Image (1200 sq ft buffer - Core Objective 3)
    post_content, post_metadata = fetch_sh_image(lat, lon, post_install_period, 1200)

    # 7.6 Handle Post-install Image Failure
    if post_content is None:
        return SatelliteAnalysisResult(
            score=0.0, details="Post-installation image fetch failed. Cannot confirm installation.",
            pre_install_panel_count=pre_count, post_install_panel_count=0, yolo_confidence=0.0,
            pv_area_sqm_est=0.0, qc_status=QCStatus.NOT_VERIFIABLE, image_metadata=pre_metadata
        )

    # 7.7 Run YOLO on Post-install Image & Generate Artifact
    post_count, post_conf, post_area, overlay_image_bytes = run_yolo_detection(post_content)

    # --- ARTIFACT STORAGE (Core Objective 5) ---
    if overlay_image_bytes:
        # Assume a storage service (like the one in services/storage.py) is available
        # You would call a function here to save the image artifact.
        # Example: save_artifact_to_storage(f"{sample_id}_overlay.jpg", overlay_image_bytes)
        pass

        # 7.8 Scoring Logic
    qc_status = QCStatus.VERIFIABLE
    pv_area_sqm_est = post_area
    score = 0.0
    details = ""

    if post_count == 0:
        score = 0.0
        details = "YOLO detected NO panels in the post-installation image."
    elif pre_count > post_count:
        score = 0.1
        details = f"Suspicious activity: Panel count DECREASED from {pre_count} to {post_count}."
    else:
        count_diff = abs(post_count - declared_panel_count)

        if count_diff <= 2:
            score = 1.0
            details = f"Panel count verified. Detected: {post_count}, Declared: {declared_panel_count}. Area: {pv_area_sqm_est:.2f} sqm."
        elif count_diff <= 10:
            score = 0.8
            details = f"Panel count is close. Detected: {post_count}, Declared: {declared_panel_count}. Area: {pv_area_sqm_est:.2f} sqm."
        else:
            score = 0.5
            details = f"Significant panel count mismatch. Detected: {post_count}, Declared: {declared_panel_count}. Area: {pv_area_sqm_est:.2f} sqm."

    # Final scoring must be weighted
    final_score = score * settings.WEIGHT_SATELLITE_ANALYSIS

    return SatelliteAnalysisResult(
        score=final_score,
        details=details,
        pre_install_panel_count=pre_count,
        post_install_panel_count=post_count,
        yolo_confidence=post_conf,
        pv_area_sqm_est=pv_area_sqm_est,
        qc_status=qc_status,
        image_metadata=post_metadata
    )