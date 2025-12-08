# In backend/api/endpoints/verifications.py

from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from typing import Annotated

from core.database import get_application_collection
# UPDATED: Import get_current_user directly (CurrentUser alias was removed from dependencies.py)
from api.dependencies import DBSession, get_current_user
from models.application import ApplicationModel, VerificationReport
from models.user import UserModel  # Used for type hinting

router = APIRouter()


@router.get(
    "/{application_id}/report",
    response_model=VerificationReport,
    tags=["verifications"]
)
async def get_verification_report(
        application_id: str,
        # CORRECTED DEPENDENCY: Use the function directly with Depends(get_current_user)
        current_user: Annotated[UserModel, Depends(get_current_user)],
        db_client: DBSession,
):
    """
    Retrieves the detailed verification report for a specific application
    if the status is 'approved', 'rejected', or 'manual_review'.
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

    # Convert the document to the full ApplicationModel for status check
    application = ApplicationModel(**app_doc)

    # UPDATED STATUS CHECK: Added "initial_application" to indicate report is not ready yet.
    if application.status in ["initial_application", "verifying"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Verification for this application is still in progress. Current status: {application.status}"
        )

    # Return the embedded report
    if application.verification_report is None:
        # Should not happen if status is final, but acts as a safeguard
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Final status reached, but report content is missing."
        )

    return application.verification_report