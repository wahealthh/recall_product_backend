from fastapi import APIRouter, status, HTTPException
from app.utils.patient import get_due_patients
from vapi import Vapi
from vapi.core.api_error import ApiError
import json

from app.schema.patient import CallHistory, Customer
from app.config.config import settings


vapi_client = Vapi(
    token=settings.VAPI_API_KEY,
)

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/call_due_patients",
    status_code=status.HTTP_200_OK,
    summary="Call due patients",
    description="Call due patients",
)
async def call_due_patients():
    due_patients = await get_due_patients()
    if not due_patients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No due patients found",
        )
    customer = Customer.model_validate(due_patients[3])
    try:
        call = vapi_client.calls.create(
            assistant_id=settings.ASSISTANT_ID,
            customer=customer,
            phone_number_id=settings.PHONE_NUMBER_ID,
            assistant_overrides={
                "variable_values": {
                    "first_name": due_patients[0]["first_name"],
                    "last_name": due_patients[0]["last_name"],
                    "dob": due_patients[0]["dob"],
                    "email": due_patients[0]["email"],
                }
            },
        )
        return call
    except ApiError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create call", "error": str(e.body)},
        )


@router.get(
    "/calls",
    status_code=status.HTTP_200_OK,
    summary="Get all calls",
    description="Retrieve all calls from Vapi",
    # response_model=list[CallHistory],
)
async def get_calls(limit: int = 40):
    try:
        calls = vapi_client.calls.list(limit=limit)
        call_objects = [call.model_dump() for call in calls]

        processed_calls = []
        for call in call_objects:
            variable_values = call.get("assistant_overrides").get("variable_values")
            minutes = 0
            costs = call.get("costs")
            if costs:
                for cost in costs:
                    if cost["type"] == "vapi":
                        minutes = cost["minutes"]
                        break
            if variable_values:
                call_info = CallHistory(
                    first_name=variable_values.get("first_name"),
                    last_name=variable_values.get("last_name"),
                    phone=call.get("customer").get("number"),
                    summary=call.get("summary"),
                    minutes=minutes,
                )
                processed_calls.append(call_info)

        return processed_calls
    except ApiError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch calls", "error": str(e.body)},
        )
