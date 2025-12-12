# deliverables/pipeline_code/main_pipeline.py

import pandas as pd
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Relative imports
from services.satellite_analysis import satellite_verification
from core.config import settings  # Needed for STORAGE_DIR

# --- FILE PATHS ---
# Assuming the input is in 'input_data/samples.csv' or similar location relative to BASE_DIR
# Change this path to match your exact input file name/location if different
INPUT_FILE = Path(__file__).resolve().parent.parent.parent / "input_data" / "samples.csv"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "deliverables" / "prediction_files"
OUTPUT_FILE = OUTPUT_DIR / f"verification_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


async def process_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the satellite verification pipeline for a single sample and formats the output.
    """
    sample_id = str(sample['sample_id'])
    lat = sample['latitude']
    lon = sample['longitude']
    declared_panels = sample['declared_panel_count']
    submission_date = sample['submission_date']  # Assumed field in input data

    print(f"--- Processing Sample ID: {sample_id} at ({lat}, {lon}) ---")

    try:
        # Run the core verification logic
        result = await satellite_verification(
            lat=lat,
            lon=lon,
            declared_panel_count=declared_panels,
            submission_date=submission_date,
            sample_id=sample_id
        )

        # Map the SatelliteAnalysisResult to the mandatory challenge output JSON format
        # This function structure is crucial for the final deliverable.
        output_record = {
            "sample_id": sample_id,
            "lat": lat,
            "lon": lon,
            "declared_panel_count": declared_panels,
            "has_solar": result.post_install_panel_count > 0,
            "confidence": result.score,  # Final weighted score
            "pv_area_sqm_est": round(result.pv_area_sqm_est, 2),
            "buffer_radius_sqft": result.final_buffer_sqft,
            "qc_status": result.qc_status,
            "bbox_or_mask": result.artifact_filename,  # Using filename as placeholder for encoded polygon/bbox
            "image_metadata": result.image_metadata,
            "details": result.details,
            "pre_install_panel_count": result.pre_install_panel_count,
            "post_install_panel_count": result.post_install_panel_count,
            "yolo_confidence_avg": round(result.yolo_confidence, 4)
        }
        return output_record

    except Exception as e:
        print(f"CRITICAL ERROR processing sample {sample_id}: {e}")
        return {
            "sample_id": sample_id,
            "lat": lat,
            "lon": lon,
            "has_solar": False,
            "confidence": 0.0,
            "qc_status": "NOT_VERIFIABLE",
            "details": f"CRITICAL PIPELINE FAILURE: {str(e)}",
            "pv_area_sqm_est": 0.0,
            "buffer_radius_sqft": 0,
            "bbox_or_mask": "",
            "image_metadata": {}
        }


async def main_pipeline():
    """
    Main function to run the batch verification pipeline.
    """
    # 1. Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Read Input Data
    try:
        # Assuming the input file is CSV (e.g., from an .xlsx export)
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_FILE}")
        return
    except Exception as e:
        print(f"Error reading input data: {e}")
        return

    # Assuming required columns exist in your CSV/Excel file:
    # ['sample_id', 'latitude', 'longitude', 'declared_panel_count', 'submission_date']
    if not all(col in df.columns for col in ['sample_id', 'latitude', 'longitude']):
        print("Error: Input file must contain 'sample_id', 'latitude', and 'longitude' columns.")
        return

    # Fill in missing dummy data for demonstration if not present
    if 'declared_panel_count' not in df.columns:
        df['declared_panel_count'] = 10  # Default for testing
        print("Warning: 'declared_panel_count' not found. Using default value 10.")
    if 'submission_date' not in df.columns:
        df['submission_date'] = datetime.now().isoformat()
        print("Warning: 'submission_date' not found. Using current date.")

    # 3. Process Samples Asynchronously
    # Convert DataFrame rows to a list of dicts for processing
    samples_to_process = df.to_dict('records')

    # Create tasks for parallel execution (important for I/O-bound tasks like API calls)
    tasks = [process_sample(sample) for sample in samples_to_process]

    # Run all tasks and wait for results
    all_results = await asyncio.gather(*tasks)

    # 4. Write Final JSON Output
    final_output = {
        "pipeline_run_time": datetime.now().isoformat(),
        "total_samples": len(all_results),
        "results": all_results
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_output, f, indent=4)

    print(f"\n✅ Pipeline completed successfully.")
    print(f"Results written to: {OUTPUT_FILE}")
    print(f"Artifacts stored in: {settings.STORAGE_DIR}")


if __name__ == "__main__":
    # Ensure all required libraries are installed:
    # pip install pandas asyncio

    # Python 3.7+ required for asyncio.run
    asyncio.run(main_pipeline())