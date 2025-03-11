from pydantic import BaseModel, EmailStr

class CreatePractice(BaseModel):
    practice_name: str
    practice_email: EmailStr
    practice_phone_number: str
    practice_address: str

    class Config:
        from_attributes = True

class ShowPractice(BaseModel):
    id: str
    practice_name: str
    practice_email: str
    practice_phone_number: str
    practice_address: str
    admin_id: str

    class Config:
        from_attributes = True 