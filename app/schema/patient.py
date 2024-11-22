from typing import Optional
from pydantic import BaseModel, Field, constr


class Patient(BaseModel):
    first_name: str
    last_name: str
    phone: str
    dob: str


class Customer(BaseModel):
    number: str = Field(description="Customer's phone number", min_length=3)
    numberE164CheckEnabled: Optional[bool] = Field(
        default=False,
        description="""Flag to toggle E164 number validation.
            False: Allows non-E164 numbers (e.g., +001234567890, 1234, abc)
            True: Allows only E164 numbers (e.g., +14155551234)
            Numbers must contain only alphanumeric chars with optional leading '+'""",
    )
    extension: Optional[str] = Field(
        default=None, description="Extension to dial after call is answered"
    )
    sipUri: Optional[str] = Field(default=None, description="SIP URI of the customer")
    name: Optional[str] = Field(
        default=None,
        description="Customer name for reference. For SIP inbound calls, extracted from From SIP header",
    )

    class Config:
        exclude_none = True
