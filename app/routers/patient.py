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
    customer = Customer.model_validate(due_patients[0])
    try:
        patient_info = due_patients[0]
        call = vapi_client.calls.create(
            assistant_id=settings.ASSISTANT_ID,
            customer=customer,
            phone_number_id=settings.PHONE_NUMBER_ID,
            assistant_overrides={
                "variable_values": {
                    "first_name": patient_info["first_name"],
                    "last_name": patient_info["last_name"],
                    "dob": patient_info["dob"],
                    "email": patient_info["email"],
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
    description="Retrieve all calls from Vapi in batches of 10",
)
async def get_calls(limit: int = 10):
    try:
        if limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be greater than 0",
            )
        BATCH_SIZE = 10
        processed_calls = []
        total_fetched = 0

        while total_fetched < limit:
            current_batch = vapi_client.calls.list(limit=BATCH_SIZE)
            if not current_batch:
                break

            for call in current_batch:
                if total_fetched >= limit:
                    break

                call_dict = call.model_dump()
                print(call_dict.get("id"))

                if call_dict is None:
                    raise ValueError("call.model_dump() returned None")

                assistant_overrides = call_dict.get("assistant_overrides", {})

                if assistant_overrides is None:
                    print("assistant_overrides is None in call_dict")
                    continue
                    # raise ValueError("assistant_overrides is None in call_dict")

                variable_values = assistant_overrides.get("variable_values", {})
                minutes = 0
                costs = call_dict.get("costs")
                if costs:
                    for cost in costs:
                        if cost["type"] == "vapi":
                            minutes = cost["minutes"]
                            break

                messages = call_dict.get("messages")
                arguments = None
                status = "Incomplete"
                stereo_recording_url = None
                if messages:
                    for message in messages:
                        if message["role"] == "tool_calls":
                            for tool_call in message["tool_calls"]:
                                if (
                                    tool_call["function"]["name"]
                                    == "sendAppointmentEmail"
                                ):
                                    arguments = json.loads(
                                        tool_call["function"]["arguments"]
                                    )
                        elif (
                            message.get("type") == "function"
                            and message["function"]["name"] == "sendAppointmentEmail"
                        ):
                            arguments = json.loads(message["function"]["arguments"])

                        if (
                            message.get("role") == "tool_call_result"
                            and message.get("name") == "sendAppointmentEmail"
                        ):
                            status = message["result"]

                if call_dict.get("stereoRecordingUrl"):
                    stereo_recording_url = call_dict.get("stereoRecordingUrl")

                if variable_values:
                    call_info = CallHistory(
                        first_name=variable_values.get("first_name"),
                        last_name=variable_values.get("last_name"),
                        phone=call_dict.get("customer", {}).get("number"),
                        summary=call_dict.get("summary"),
                        minutes=minutes,
                        appointment_date=(
                            arguments.get("appointment_data", {}).get(
                                "appointment_date"
                            )
                            if arguments
                            else None
                        ),
                        appointment_time=(
                            arguments.get("appointment_data", {}).get(
                                "appointment_time"
                            )
                            if arguments
                            else None
                        ),
                        call_date=call_dict.get("created_at"),
                        status=status,
                        stereo_recording_url=stereo_recording_url,
                    )
                    processed_calls.append(call_info)
                    total_fetched += 1

        return processed_calls
    except ApiError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch calls", "error": str(e.body)},
        )


@router.delete(
    "/calls/{call_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a call",
    description="Delete a specific call from Vapi",
)
async def delete_call(call_id: str):
    try:
        return vapi_client.calls.delete(id=call_id)
    except ApiError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to delete call", "error": str(e.body)},
        )
