from typing import List
from fastapi import APIRouter, HTTPException, status
import requests

from app.config.config import settings

HEADERS = {"x-api-key": settings.POSTMAN_API_KEY}
BASE_URL = settings.POSTMAN_BASE_URL


async def get_due_patients_util():
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
