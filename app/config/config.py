#!/usr/bin/python
"""sets environment variable using pydantic BaseSettings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr


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


settings = Settings()
