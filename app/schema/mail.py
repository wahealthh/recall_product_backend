from pydantic import BaseModel, EmailStr
from typing import Optional


class AppointmentEmail(BaseModel):
    patient_name: str
    patient_email: EmailStr
    appointment_date: str
    appointment_time: str
    gp_name: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "patient_name": "John Doe",
                "patient_email": "john@example.com",
                "appointment_date": "2024-03-15",
                "appointment_time": "2:30 PM",
                "doctor_name": "Dr. Smith",
                "location": "Main Clinic",
                "notes": "Regular checkup",
            }
        }
