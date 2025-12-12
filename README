Surya Saathi – Deliverables
This directory contains all the submission-ready artefacts for the Surya Saathi: AI-Powered Solar Subsidy Verification System. It includes the complete inference pipeline, environment specification, trained model weights, prediction files, artefacts, and training logs required to reproduce and evaluate the YOLOv11-based solar panel detection system.

Structure
text
deliverables/
├── pipeline_code/           # Core batch inference pipeline (no web stack)
│   ├── main_pipeline.py     # Entry point to run YOLOv11 inference on samples.csv
│   ├── core/                # Pipeline configuration and shared settings
│   ├── models/              # Pydantic / data models used in pipeline
│   ├── services/            # Detection and verification logic (imported from backend)
│   └── utils/               # Helper utilities (paths, I/O, etc.)
│
├── environment_details/     # Reproducible environment specification
│   ├── requirements.txt     # pip requirements (FastAPI, Torch, Ultralytics, etc.)
│   ├── environment.yml      # Conda environment file (Python 3.10 + CUDA stack)
│   └── python_version.txt   # Python version used (3.10)
│
├── trained_model_file/      # Trained YOLOv11 model weights
│   └── best.pt              # ~5.2MB YOLOv11 nano checkpoint
│
├── prediction_files/        # Pipeline output (JSON predictions)
│   └── test_predictions.json  # Placeholder/example JSON output
│
├── model_training_logs/     # Training metrics for YOLO model
│   └── training_metrics.csv # Epoch-wise YOLOv11 training metrics (box/cls/dfl, mAP, etc.)
│
└── artefacts/               # Visual/qualitative artefacts
    └── sample_images/       # Example images for qualitative inspection
The pipeline reads input from:

text
input_data/
└── samples.csv              # Sample input list (lat/lon/panel count/date)
Environment Setup
All instructions below assume you are at the repository root:

bash
cd AlgoMinds-SuryaSaathi
Python Version
bash
cat deliverables/environment_details/python_version.txt
# 3.10
python --version
# Ensure: Python 3.10.x
Option 1 – Conda (Recommended)
bash
# Create environment
conda env create -f deliverables/environment_details/environment.yml

# Activate
conda activate surya-saathi

# Quick sanity check
python -c "from ultralytics import YOLO; print('YOLO OK')"
Option 2 – Virtualenv + pip
bash
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r deliverables/environment_details/requirements.txt

python -c "from ultralytics import YOLO; print('YOLO OK')"
Input Format
The deliverables pipeline is batch, file-based and uses a CSV located at input_data/samples.csv.

Current example in your repo:

text
sample_id,latitude,longitude,declared_panel_count,submission_date
"1001    ",12.9716,77.5946,10,01-03-2024
Required Columns
Column	Type	Description
sample_id	str	Unique ID for the sample (application / location)
latitude	float	Latitude of installation location
longitude	float	Longitude of installation location
declared_panel_count	int	Panels claimed in application
submission_date	str	Submission date (accepted by pipeline as string)
main_pipeline.py will:

Validate that sample_id, latitude, longitude exist.

Fill declared_panel_count with a default (10) if missing.

Fill submission_date with current datetime if missing.

Running the Pipeline
The entire submission pipeline (YOLOv11 detection + JSON output) is driven by:

text
deliverables/pipeline_code/main_pipeline.py
Basic Run
From the repo root:

bash
conda activate surya-saathi  # or your venv
python deliverables/pipeline_code/main_pipeline.py
What happens:

Input Read

Reads input_data/samples.csv.

Each row is converted into a sample dictionary.

Per-sample Processing

For each sample:

sample_id, latitude, longitude, declared_panel_count, submission_date extracted.

Calls:

python
result = await satellite_verification(
    lat=lat,
    lon=lon,
    declared_panel_count=declared_panels,
    submission_date=submission_date,
    sample_id=sample_id
)
satellite_verification(...) (in services/satellite_analysis.py) performs:

YOLOv11 detection using best.pt

Panel count estimation (pre- vs post-installation)

Area estimation, QC status determination

Returns a structured SatelliteAnalysisResult.

JSON Output

For each sample, the pipeline writes a record like:

json
{
  "sample_id": "1001",
  "lat": 12.9716,
  "lon": 77.5946,
  "declared_panel_count": 10,
  "has_solar": true,
  "confidence": 0.82,
  "pv_area_sqm_est": 34.5,
  "buffer_radius_sqft": 500,
  "qc_status": "VERIFIED",
  "bbox_or_mask": "bbox_1001.png",
  "image_metadata": {...},
  "details": "Solar installation verified...",
  "pre_install_panel_count": 0,
  "post_install_panel_count": 9,
  "yolo_confidence_avg": 0.78
}
The full JSON structure written is:

json
{
  "pipeline_run_time": "2025-12-12T15:30:45Z",
  "total_samples": N,
  "results": [ ... one record per sample ... ]
}
Output Location

Output file path pattern:

text
deliverables/prediction_files/verification_predictions_YYYYMMDD_HHMMSS.json
Example:

bash
ls deliverables/prediction_files/
# verification_predictions_20251212_153045.json
Components in Deliverables
1. pipeline_code/
Core non-HTTP pipeline code hooked to the trained YOLO model.

main_pipeline.py

Asynchronous batch runner.

Reads CSV, spawns process_sample tasks, aggregates results, writes JSON.

core/

Expected to include config.py with constants like storage directories, etc.

services/

satellite_analysis.py (imported from backend logic)

Encapsulates YOLOv11 model loading (best.pt) and inference.

Computes panel counts, average confidence, QC status, and artefact filenames.

Other service modules mirror the backend service layer but are consumed here only for inference.

models/

Pydantic-style models/DTOs for SatelliteAnalysisResult and similar.

utils/

Shared helper utilities (paths, logging, etc.).

Note: For the challenge, you do not need to run FastAPI; the only entry point required is main_pipeline.py.

2. environment_details/
Environment reproducibility and version control:

requirements.txt

pip-based environment. Key packages:

torch, torchvision, ultralytics – YOLOv11 and PyTorch

opencv-python, pillow – image processing

pvlib, pytz – solar position/shadow analysis

plus API/infra dependencies (FastAPI, Motor, etc., inherited from backend stack).

environment.yml

Conda-based environment:

python=3.10

PyTorch + CUDA

Additional pip packages via pip: section.

python_version.txt

Explicitly pins Python 3.10.

This matches the deliverable requirement: clearly specified environment for both pip and conda.

3. trained_model_file/
best.pt

Trained YOLOv11 nano checkpoint (~5.2MB).

Used by satellite_analysis.py during inference.

Represents the final model after 50 epochs of training (see logs below).

This satisfies the “Trained model file (.pt)” requirement.

4. model_training_logs/
training_metrics.csv

CSV containing YOLO training metrics for 50 epochs with columns like:

epoch, time

train/box_loss, train/cls_loss, train/dfl_loss

metrics/precision(B), metrics/recall(B)

metrics/mAP50(B), metrics/mAP50-95(B)

val/box_loss, val/cls_loss, val/dfl_loss

lr/pg0, lr/pg1, lr/pg2

Example (epoch 50):

mAP50(B) ≈ 0.824

Precision ≈ 0.765

Recall ≈ 0.787

Use this file to:

Plot loss/metric curves.

Verify convergence and final performance.

Demonstrate training process for the submission.

5. prediction_files/
test_predictions.json

Placeholder/example file to show expected JSON structure.

Real prediction files will be named:

text
verification_predictions_YYYYMMDD_HHMMSS.json
Generated by main_pipeline.py after processing all rows in input_data/samples.csv.

This satisfies “Prediction files (.json)” requirement.

6. artefacts/
sample_images/

Designed to contain:

Sample satellite images.

Visual overlays (YOLO detections, bounding boxes, masks, etc.).

You can export figures like:

detection_SAMPLEID.png

confusion_matrix.png

training_curves.png

These satisfy the “Artefacts for training dataset (.jpg, .png etc)” requirement.

Typical End-to-End Flow
Prepare Environment

Create and activate conda/venv with dependencies.

Prepare Input

Edit input_data/samples.csv with real sample locations and metadata.

Run Pipeline

bash
python deliverables/pipeline_code/main_pipeline.py
Inspect Outputs

JSON predictions in deliverables/prediction_files/.

Visual/sample artefacts in deliverables/artefacts/.

Refer to Model Card (separate file)

deliverables/model_card/MODEL_CARD.md (if you add it there) contains:

Data used, assumptions, logic.

Known limitations/bias.

Failure modes and retraining guidance.

Notes for Evaluators
This deliverables directory is self-contained for:

Running inference on a CSV input file.

Inspecting model behaviour via predictions and artefacts.

Reproducing the environment and understanding training dynamics via logs.

The frontend and backend directories implement a full product (mobile app + API),
but are not required to evaluate the ML deliverables themselves.

For any issues, check:

Paths in main_pipeline.py (input and output locations).

Environment versions in environment_details/.

Model file presence in trained_model_file/best.pt.

This README is focused strictly on deliverables, as requested.
