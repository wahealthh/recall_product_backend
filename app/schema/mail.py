from pydantic import BaseModel, EmailStr
from typing import Optional


class AppointmentData(BaseModel):
    notes: Optional[str] = None
    gp_name: Optional[str] = None
    patient_email: EmailStr
    appointment_date: str
    appointment_time: str
    patient_name: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "notes": "Hypertension check-up",
                "gp_name": "Ross Road Medical Centre",
                "patient_email": "0xnuru@gmail.com",
                "appointment_date": "02-03-2025",
                "appointment_time": "10:00",
                "patient_name": "John Doe",
            }
        }
    }
