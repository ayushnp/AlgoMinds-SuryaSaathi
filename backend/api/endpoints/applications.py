import os
from datetime import datetime
from typing import Annotated, Dict, Any  # Added Dict, Any for app_doc typing

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Form, UploadFile
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# --- CORE IMPORTS ---
from core.database import get_application_collection
from core.config import settings
from api.dependencies import DBSession, CurrentUser
from models.user import UserModel, PyObjectId
# CORRECTED IMPORT: Import the new model InitialApplicationCreate
from models.application import ApplicationModel, InitialApplicationCreate, PhotoMetadata
from services.ml_pipeline import run_verification_pipeline
from services.storage import save_uploaded_files, get_storage_path

router = APIRouter()


# --- 1. INITIAL APPLICATION SUBMISSION (Step 1: POST /api/v1/applications/apply) ---

@router.post("/apply", status_code=status.HTTP_201_CREATED)
async def initial_application(
        user_in: InitialApplicationCreate,  # Uses the detailed Pydantic model
        current_user: CurrentUser,
        db_client: DBSession,
):
    """
    Submits a detailed initial application, creating a placeholder document
    and returning a unique Application ID for later verification.
    """
    app_collection = get_application_collection()

    # Create the Database Document with all detailed application information
    app_doc: Dict[str, Any] = {  # Use Dict[str, Any] for flexibility
        "user_id": current_user.id,

        # Details from the initial form
        "applicant_name": user_in.applicant_name,
        "applicant_phone": user_in.applicant_phone,
        "address": user_in.address,
        "system_capacity_kw": user_in.system_capacity_kw,
        "declared_panel_count": user_in.declared_panel_count,
        "installer_company": user_in.installer_company,
        "installer_contact": user_in.installer_contact,
        "preferred_verification_date": user_in.preferred_verification_date,

        # Verification fields are set to None initially
        "registered_lat": None,
        "registered_lon": None,
        "wide_rooftop_photo": None,
        "serial_number_photo": None,
        "inverter_photo": None,

        "status": "initial_application",  # Set to initial status
        "submission_date": datetime.now().isoformat(),
        "verification_report": None,
    }

    insert_result = await app_collection.insert_one(app_doc)
    app_id = str(insert_result.inserted_id)

    return {
        "application_id": app_id,
        "message": "Initial application submitted. Please proceed to verification after installation."
    }


# --- 2. VERIFICATION SUBMISSION (Step 2: POST /api/v1/applications/submit) ---

@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_verification(
        background_tasks: BackgroundTasks,
        current_user: CurrentUser,
        # The ID from the initial step is passed as a Form field (Crucial for matching)
        application_id: Annotated[str, Form()],
        # Final Verification Data
        registered_lat: Annotated[float, Form()],
        registered_lon: Annotated[float, Form()],
        wide_rooftop_photo: UploadFile,
        serial_number_photo: UploadFile,
        inverter_photo: UploadFile,

        db_client: DBSession,
):
    """
    Submits post-installation photos and GPS data for a pre-existing application ID.
    Triggers the intensive AI verification pipeline asynchronously.
    """
    app_collection = get_application_collection()
    user_id_str = str(current_user.id)

    # 1. Validate and Fetch Existing Application
    try:
        app_object_id = ObjectId(application_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Application ID format.")

    # Query by ID and ensure it belongs to the current user
    app_doc = await app_collection.find_one(
        {"_id": app_object_id, "user_id": current_user.id}
    )

    if app_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Application not found or does not belong to user.")

    # Ensure it's ready for verification (i.e., status is initial_application or rejected)
    if app_doc.get("status") not in ["initial_application", "rejected"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Application status is {app_doc.get('status')}. Cannot submit verification photos.")

    # 2. Save Files to Storage
    try:
        file_keys = await save_uploaded_files(
            user_id_str=user_id_str,
            files={
                "wide_rooftop": wide_rooftop_photo,
                "serial_number": serial_number_photo,
                "inverter": inverter_photo,
            }
        )
    except Exception as e:
        print(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save uploaded files."
        )

    # 3. Update the Database Document with new verification data
    # Create PhotoMetadata objects for consistency, though the schema is permissive
    wide_photo_metadata = PhotoMetadata(s3_key=file_keys["wide_rooftop"])
    serial_photo_metadata = PhotoMetadata(s3_key=file_keys["serial_number"])
    inverter_photo_metadata = PhotoMetadata(s3_key=file_keys["inverter"])

    update_data = {
        "registered_lat": registered_lat,
        "registered_lon": registered_lon,
        "wide_rooftop_photo": wide_photo_metadata.model_dump(),
        "serial_number_photo": serial_photo_metadata.model_dump(),
        "inverter_photo": inverter_photo_metadata.model_dump(),
        "status": "verifying",
    }

    await app_collection.update_one(
        {"_id": app_object_id},
        {"$set": update_data}
    )

    # Retrieve the full document to pass to the ML pipeline (includes initial details)
    updated_app_doc = await app_collection.find_one({"_id": app_object_id})

    # 4. 🚀 Trigger Asynchronous Verification Pipeline
    background_tasks.add_task(
        run_verification_pipeline,
        application_id,
        updated_app_doc,
        current_user.email
    )

    return {
        "application_id": application_id,
        "message": "Verification photos submitted successfully. AI verification is now running."
    }


# --- Endpoint to retrieve application status/report (Remains the same) ---

@router.get("/{application_id}", response_model=ApplicationModel)
async def get_application_details(
        application_id: str,
        current_user: CurrentUser,
        db_client: DBSession,
):
    """
    Retrieves the status and verification report for a specific application.
    """
    app_collection = get_application_collection()

    try:
        app_object_id = ObjectId(application_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Application ID format.")

    # Query by ID and ensure it belongs to the current user
    app_doc = await app_collection.find_one(
        {"_id": app_object_id, "user_id": current_user.id}
    )

    if app_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

    return ApplicationModel(**app_doc)