#!/usr/bin/env python

import re
from pydantic import BaseModel, EmailStr, SecretStr, model_validator


class CreateAdmin(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password1: SecretStr
    password2: SecretStr

    class Config:
        from_attributes = True
