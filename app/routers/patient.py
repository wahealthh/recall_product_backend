from datetime import datetime
from fastapi import APIRouter, status, HTTPException, Depends, Request
from app.utils.patient import get_due_patients_util
from vapi import Vapi
from vapi.core.api_error import ApiError
import json
from app.utils.limiter import limiter
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from app.schema.patient import CallHistory, Customer, Patient, DemoPatient
from app.config.config import settings
from app.engine.load import load
from app.models.recall_group import RecallGroup
from app.models.recall_patient import RecallPatient
from app.models.practice import Practice
from app.utils.auth import verify_admin


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
    "/groups/{group_id}/call",
    status_code=status.HTTP_200_OK,
    summary="Call patients in a group",
    description="Call patients from a specific recall group",
)
async def call_due_patients(
    group_id: str,
    call_context: Optional[str] = None,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    current_datetime = datetime.now()
    
    # Get the practice for this admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin_data["user_id"]).first()
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found for this admin"
        )
    
    # Get the group with a join to its practice to verify admin access
    group = db.query_eng(RecallGroup).filter(
        RecallGroup.id == group_id,
        RecallGroup.practice_id == practice.id
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recall group not found or you don't have permission to access it"
        )
    
    # Fetch patients from the database based on the group_id
    patients = db.query_eng(RecallPatient).filter(
        RecallPatient.recall_group_id == group_id
    ).all()
    
    if not patients:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No patients found in group with ID: {group_id}",
        )
    
    call_results = []
    failed_calls = []
    
    for patient in patients:
        customer = Customer(
            number=patient.number,
        )
        try:
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
                    "notes": patient.notes,
                    "call_context": call_context
                }
            },
        )
            call_results.append({
                "patient": f"{patient.first_name} {patient.last_name}",
                "call_id": call.id,
                "status": call.status,
                "created_at": call.created_at
            })
        except ApiError as e:
            error_detail = str(e.body) if hasattr(e, "body") else str(e)
            failed_calls.append({
                "patient": f"{patient.first_name} {patient.last_name}",
                "error": error_detail
            })
    
    return {
        "success": len(call_results),
        "failed": len(failed_calls),
        "calls": call_results,
        "errors": failed_calls,
        "group": group.name
    }


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
                        if message.get("role") == "tool_calls" and "tool_calls" in message:
                            for tool_call in message.get("tool_calls", []):
                                if (
                                    isinstance(tool_call, dict) 
                                    and "function" in tool_call
                                    and "name" in tool_call["function"]
                                    and tool_call["function"]["name"] == "sendAppointmentEmail"
                                    and "arguments" in tool_call["function"]
                                ):
                                    arguments = json.loads(
                                        tool_call["function"]["arguments"]
                                    )
                        elif (
                            message.get("type") == "function"
                            and "function" in message
                            and "name" in message["function"]
                            and message["function"]["name"] == "sendAppointmentEmail"
                            and "arguments" in message["function"]
                        ):
                            arguments = json.loads(message["function"]["arguments"])

                        if (
                            message.get("role") == "tool_call_result"
                            and message.get("name") == "sendAppointmentEmail"
                            and "result" in message
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

