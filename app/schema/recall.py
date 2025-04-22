from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
import datetime


class PatientBase(BaseModel):
    """Base model for patient data"""
    first_name: str
    last_name: str
    email: str
    number: str
    dob: str
    notes: Optional[str] = None


class CreateRecallPatient(PatientBase):
    """Schema for creating a recall patient"""
    pass


class RecallPatientResponse(PatientBase):
    """Schema for responding with recall patient data"""
    id: str
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True


class BatchPatientCreateResponse(BaseModel):
    """Response schema for batch patient creation"""
    success_count: int
    failed_count: int
    patients: List[RecallPatientResponse] = []
    errors: List[dict] = []
    

class CreateRecallGroup(BaseModel):
    """Schema for creating a recall group"""
    name: str
    description: Optional[str] = None


class RecallGroupResponse(BaseModel):
    """Schema for responding with recall group data"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime.datetime
    practice_id: str
    
    class Config:
        from_attributes = True


class RecallGroupWithPatientsResponse(RecallGroupResponse):
    """Schema for responding with recall group including its patients"""
    patients: List[RecallPatientResponse] = []
    
    class Config:
        from_attributes = True


class CSVPatientImport(BaseModel):
    """Schema for importing patients from CSV file"""
    file_content: str 