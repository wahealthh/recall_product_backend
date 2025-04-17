import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.engine.load import load
from app.models import RecallGroup, RecallPatient, Practice
from app.models.admin import Admin
from app.schema.recall import (
    CreateRecallGroup, 
    CreateRecallPatient, 
    RecallGroupResponse, 
    RecallPatientResponse,
    RecallGroupWithPatientsResponse,
    CSVPatientImport,
    BatchPatientCreateResponse
)
from app.utils.auth import verify_admin

router = APIRouter(prefix="/recall", tags=["Recall"])


@router.post(
    "/groups", 
    status_code=status.HTTP_201_CREATED, 
    response_model=RecallGroupResponse
)
async def create_recall_group(
    request: CreateRecallGroup,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Create a new recall group"""
    # Verify that the practice exists and belongs to the admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin_data["user_id"]).first()
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found or you don't have permission to access it"
        )
    
    new_group = RecallGroup(
        name=request.name,
        description=request.description,
        practice_id=practice.id
    )
    
    try:
        db.add(new_group)
        db.commit()
        db.refresh(new_group)
        return new_group
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recall group: {str(e)}"
        )


@router.get(
    "/groups", 
    status_code=status.HTTP_200_OK, 
    response_model=List[RecallGroupResponse]
)
async def get_recall_groups(
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Get all recall groups for the admin's practice"""
    # Get the practice for this admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin_data["user_id"]).first()
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found for this admin"
        )
    
    # Get all recall groups for the practice
    groups = db.query_eng(RecallGroup).filter(
        RecallGroup.practice_id == practice.id
    ).all()
    
    return groups


@router.get(
    "/groups/{group_id}", 
    status_code=status.HTTP_200_OK, 
    response_model=RecallGroupWithPatientsResponse
)
async def get_recall_group(
    group_id: str,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Get a specific recall group with its patients"""
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
    
    return group


@router.delete(
    "/groups/{group_id}", 
    status_code=status.HTTP_200_OK
)
async def delete_recall_group(
    group_id: str,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Delete a recall group and all its patients"""
    # Get the practice for this admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin_data["user_id"]).first()
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found for this admin"
        )
    
    # Get the group for the practice
    group = db.query_eng(RecallGroup).filter(
        RecallGroup.id == group_id,
        RecallGroup.practice_id == practice.id
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recall group not found or you don't have permission to access it"
        )
    
    try:
        db.delete(group)
        db.commit()
        return {"message": f"Recall group '{group.name}' deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete recall group: {str(e)}"
        )


@router.post(
    "/groups/{group_id}/patients", 
    status_code=status.HTTP_201_CREATED, 
    response_model=BatchPatientCreateResponse
)
async def add_patients_to_group(
    group_id: str,
    patients: List[CreateRecallPatient],
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Add multiple patients to a recall group"""
    # Get the practice for this admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin_data["user_id"]).first()
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found for this admin"
        )
    
    # Get the group for the practice
    group = db.query_eng(RecallGroup).filter(
        RecallGroup.id == group_id,
        RecallGroup.practice_id == practice.id
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recall group not found or you don't have permission to access it"
        )
    
    # Track results
    result = BatchPatientCreateResponse(success_count=0, failed_count=0)
    
    for patient_data in patients:
        try:
            new_patient = RecallPatient(
                first_name=patient_data.first_name,
                last_name=patient_data.last_name,
                email=patient_data.email,
                number=patient_data.number,
                dob=patient_data.dob,
                notes=patient_data.notes,
                recall_group_id=group_id
            )
            
            db.add(new_patient)
            db.commit()
            db.refresh(new_patient)
            
            result.success_count += 1
            result.patients.append(new_patient)
        except Exception as e:
            db.rollback()
            result.failed_count += 1
            result.errors.append({
                "patient": f"{patient_data.first_name} {patient_data.last_name}",
                "error": str(e)
            })
    
    if result.success_count == 0 and result.failed_count > 0:
        # If all patients failed, return a 500 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add all {result.failed_count} patients to group"
        )
    
    return result


@router.post(
    "/groups/{group_id}/patient", 
    status_code=status.HTTP_201_CREATED, 
    response_model=RecallPatientResponse
)
async def add_single_patient_to_group(
    group_id: str,
    patient: CreateRecallPatient,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Add a single patient to a recall group"""
    # Get the practice for this admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin_data["user_id"]).first()
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found for this admin"
        )
    
    # Get the group for the practice
    group = db.query_eng(RecallGroup).filter(
        RecallGroup.id == group_id,
        RecallGroup.practice_id == practice.id
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recall group not found or you don't have permission to access it"
        )
    
    new_patient = RecallPatient(
        first_name=patient.first_name,
        last_name=patient.last_name,
        email=patient.email,
        number=patient.number,
        dob=patient.dob,
        notes=patient.notes,
        recall_group_id=group_id
    )
    
    try:
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        return new_patient
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add patient to group: {str(e)}"
        )


@router.post(
    "/groups/{group_id}/import-csv", 
    status_code=status.HTTP_201_CREATED
)
async def import_patients_from_csv(
    group_id: str,
    request: CSVPatientImport,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Import multiple patients from a CSV file"""
    # Get the practice for this admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin_data["user_id"]).first()
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found for this admin"
        )
    
    # Get the group for the practice
    group = db.query_eng(RecallGroup).filter(
        RecallGroup.id == group_id,
        RecallGroup.practice_id == practice.id
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recall group not found or you don't have permission to access it"
        )
    
    # Process CSV data
    csv_file = io.StringIO(request.file_content)
    csv_reader = csv.DictReader(csv_file)
    
    required_fields = ["first_name", "last_name", "email", "number", "dob"]
    added_patients = 0
    errors = []
    
    try:
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header row
            # Check if all required fields are present
            missing_fields = [field for field in required_fields if field not in row or not row[field]]
            if missing_fields:
                errors.append(f"Row {row_num}: Missing required fields - {', '.join(missing_fields)}")
                continue
                
            # Create the patient
            new_patient = RecallPatient(
                first_name=row["first_name"],
                last_name=row["last_name"],
                email=row["email"],
                number=row["number"],
                dob=row["dob"],
                notes=row.get("notes"),  # Get notes if available
                recall_group_id=group_id
            )
            
            db.add(new_patient)
            added_patients += 1
        
        # Commit all changes if no errors occurred
        if not errors:
            db.commit()
            return {
                "message": f"Successfully imported {added_patients} patients",
                "imported_count": added_patients
            }
        else:
            # If there were any errors, commit the successful ones and return the errors
            db.commit()
            return {
                "message": f"Imported {added_patients} patients with {len(errors)} errors",
                "imported_count": added_patients,
                "errors": errors
            }
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import patients: {str(e)}"
        )


@router.delete(
    "/patients/{patient_id}", 
    status_code=status.HTTP_200_OK
)
async def delete_patient_from_group(
    patient_id: str,
    admin_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Delete a patient from a recall group"""
    # Get the practice for this admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin_data["user_id"]).first()
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found for this admin"
        )
        
    # Get the patient with a join to verify it belongs to a group in the admin's practice
    patient = db.query_eng(RecallPatient).join(
        RecallGroup, RecallPatient.recall_group_id == RecallGroup.id
    ).filter(
        RecallPatient.id == patient_id,
        RecallGroup.practice_id == practice.id
    ).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or you don't have permission to delete it"
        )
    
    try:
        db.delete(patient)
        db.commit()
        return {"message": f"Patient {patient.first_name} {patient.last_name} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete patient: {str(e)}"
        ) 