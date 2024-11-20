from typing import List
from fastapi import APIRouter, HTTPException, status
import requests
import os
from dotenv import load_dotenv

from app.schema.patient import Patient

load_dotenv()

HEADERS = {"x-api-key": os.getenv("POSTMAN_API_KEY")}
BASE_URL = os.getenv("POSTMAN_BASE_URL")


router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/due_patients",
    response_model=List[Patient],
    status_code=status.HTTP_200_OK,
    summary="Get all due patients",
    description="Retrieve a list of patients who are due for recall",
)
async def get_due_patients():
    """
    Retrieve patients who are due for recall.

    Returns:
        List[Patient]: List of patients due for recall

    Raises:
        HTTPException: If the external API request fails
    """
    try:
        response = requests.get(
            f"{BASE_URL}/recall_patients",
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch due patients: {str(e)}",
        )
