#!/usr/bin/python
"""sets environment variable using pydantic BaseSettings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """contains all required env settings loaded from .env"""

    model_config = SettingsConfigDict(env_file="../../.env", env_file_encoding="utf-8")

    # email settings
    SENDGRID_API_KEY: str
    SENDER_EMAIL: EmailStr
    PHONE_NUMBER_ID: str
    ASSISTANT_ID: str
    VAPI_API_KEY: str
    POSTMAN_API_KEY: str
    POSTMAN_BASE_URL: str

    project_name: str = "WA Health"

    #  database settings
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: str
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "https://wahealth.co.uk",
        "https://www.wahealth.co.uk",
        "http://localhost:5174",
        "http://localhost:5173",
        "https://wa-health-pwa.onrender.com",
        "http://localhost:8001",
        "https://app.wahealth.co.uk",
        "http://localhost:8000",
    ]
    
    # Authentication service settings
    AUTH_SERVICE_URL: str = "https://auth.wahealth.co.uk"
    AUTH_TOKEN_URL: str = "/auth/token"
    AUTH_VERIFY_TOKEN_URL: str = "/auth/verify_token"
    AUTH_REGISTER_URL: str = "/auth/register"
    
    # VAPI settings
    VAPI_BASE_URL: str = "https://api.vapi.ai/"


settings = Settings()
