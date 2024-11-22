from pydantic import BaseModel, EmailStr
from typing import Optional


class AppointmentData(BaseModel):
    notes: Optional[str] = None
    gp_name: Optional[str] = None
    patient_email: EmailStr
    appointment_date: str
    appointment_time: str
    patient_name: Optional[str] = None


class BotEmailRequest(BaseModel):
    appointment_data: AppointmentData

    class Config:
        json_schema_extra = {
            "example": {
                "appointment_data": {
                    "notes": "Hypertension check-up",
                    "gp_name": "Ross Road Medical Centre",
                    "patient_email": "patient@example.com",
                    "appointment_date": "Monday",
                    "appointment_time": "2 PM",
                    "patient_name": "John Doe",
                }
            }
        }
