from pydantic import BaseModel


class Patient(BaseModel):
    first_name: str
    last_name: str
    phone: str
    dob: str
