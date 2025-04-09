from datetime import datetime
from fastapi import APIRouter, status, HTTPException, Depends, Request
from app.utils.patient import get_due_patients_util
from vapi import Vapi
from vapi.core.api_error import ApiError
import json
from app.utils.limiter import limiter

from app.schema.patient import CallHistory, Customer, Patient, DemoPatient
from app.config.config import settings


vapi_client = Vapi(
    token=settings.VAPI_API_KEY,
)

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "/due_patients",
    status_code=status.HTTP_200_OK,
    summary="Get due patients",
    description="Get due patients",
)
async def get_due_patients():
    return await get_due_patients_util()


@router.post(
    "/call_due_patients",
    status_code=status.HTTP_200_OK,
    summary="Call due patients",
    description="Call due patients",
)
async def call_due_patients():
    current_datetime = datetime.now()
    due_patients = await get_due_patients()
    if not due_patients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No due patients found",
        )
    customer = Customer.model_validate(due_patients[15])
    try:
        patient_info = due_patients[15]
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
                    "current_date": current_datetime.strftime("%Y-%m-%d"),
                    "current_day": current_datetime.strftime("%A"),
                }
            },
        )
        return call
    except ApiError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create call", "error": str(e.body)},
        )


@router.post(
    "/call_patient",
    status_code=status.HTTP_200_OK,
    summary="Call a single patient",
    description="Initiate a call to a specific patient using their information",
)
async def call_patient(patient: Patient):
    current_datetime = datetime.now()
    try:
        customer = Customer(
            number=patient.number,
        )

        call = vapi_client.calls.create(
            assistant_id=settings.ASSISTANT_ID,
            customer=customer,
            phone_number_id=settings.PHONE_NUMBER_ID,
            assistant_overrides={
                "variable_values": {
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "dob": patient.dob,
                    "email": patient.email,
                    "current_date": current_datetime.strftime("%Y-%m-%d"),
                    "current_day": current_datetime.strftime("%A"),
                }
            },
        )
        return call
    except ApiError as e:
        error_detail = str(e.body) if hasattr(e, "body") else str(e)
        raise HTTPException(
            status_code=(
                e.status_code
                if hasattr(e, "status_code")
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail={
                "message": "Failed to create call",
                "error": error_detail,
                "patient": patient.model_dump(),
            },
        )


@router.get(
    "/calls",
    status_code=status.HTTP_200_OK,
    summary="Get all calls",
    description="Retrieve all calls from Vapi in batches of 10",
)
async def get_calls(limit: int = 1):
    try:
        print(f"[DEBUG] Starting get_calls with limit: {limit}")
        if limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be greater than 0",
            )
        BATCH_SIZE = 10 if limit > 10 else limit
        processed_calls = []
        total_fetched = 0

        while total_fetched < limit:
            print(f"[DEBUG] Fetching batch, total_fetched: {total_fetched}, limit: {limit}")
            current_batch = vapi_client.calls.list(limit=BATCH_SIZE)
            print(f"[DEBUG] Received batch with {len(current_batch) if current_batch else 0} calls")
            if not current_batch:
                print("[DEBUG] Empty batch received, breaking loop")
                break

            for call in current_batch:
                if total_fetched >= limit:
                    print("[DEBUG] Reached limit, breaking loop")
                    break

                call_dict = call.model_dump()
                print(f"[DEBUG] Processing call with ID: {call_dict.get('id')}")

                if call_dict is None:
                    print("[DEBUG] ERROR: call.model_dump() returned None")
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
                        id=call_dict.get("id"),
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
                    print(f"[DEBUG] Added call to processed_calls, total_fetched now: {total_fetched}")
                else:
                    print(f"[DEBUG] Skipping call {call_dict.get('id')} - no variable_values")
                    total_fetched += 1

        print(f"[DEBUG] Returning {len(processed_calls)} processed calls")
        return processed_calls
    except ApiError as e:
        print(f"[DEBUG] ApiError: {str(e)}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to fetch calls", "error": str(e.body)},
        )

@router.get(
    "/calls/{call_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single call",
    description="Retrieve a specific call from Vapi using its ID",
)
async def get_call(call_id: str):
    try:
        call = vapi_client.calls.get(id=call_id)
        return call.model_dump()
    except ApiError as e:
        error_detail = str(e.body) if hasattr(e, "body") else str(e)
        raise HTTPException(
            status_code=(
                e.status_code
                if hasattr(e, "status_code")
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail={
                "message": "Failed to fetch call",
                "error": error_detail,
                "call_id": call_id,
            },
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


@router.post(
    "/demo/call",
    status_code=status.HTTP_200_OK,
    summary="Demo endpoint for calling a patient",
    description="Simplified endpoint for demo purposes to call a patient with minimal information",
)
@limiter.limit("3/hour")
async def demo_call_patient(patient: DemoPatient, request: Request):
    current_datetime = datetime.now()
    try:
        customer = Customer(
            number=patient.number,
        )

        call = vapi_client.calls.create(
            assistant_id=settings.ASSISTANT_ID,
            customer=customer,
            phone_number_id=settings.PHONE_NUMBER_ID,
            assistant_overrides={
                "variable_values": {
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "dob": patient.dob,
                    "email": patient.email,
                    "current_date": current_datetime.strftime("%Y-%m-%d"),
                    "current_day": current_datetime.strftime("%A"),
                }
            },
        )
        
        return {
            "success": True,
            "message": f"Demo call initiated to {patient.first_name} {patient.last_name} at {patient.number}",
            "call_id": call.id,
            "call_status": call.status,
            "timestamp": datetime.now().isoformat(),
        }
    except ApiError as e:
        error_detail = str(e.body) if hasattr(e, "body") else str(e)
        raise HTTPException(
            status_code=(
                e.status_code
                if hasattr(e, "status_code")
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail={
                "message": "Failed to create demo call",
                "error": error_detail,
                "patient": patient.model_dump(),
            },
        )

