#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import httpx

from app.config.config import settings
from app.engine.load import load
from app.models.admin import Admin
from app.schema.admin import CreateAdmin
from app.utils.auth import verify_admin, verify_token


router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: CreateAdmin, 
    http_request: Request, 
    db: Session = Depends(load)
):
    """
    Two-step registration process:
    1. Register with auth service to create user credentials
    2. Create admin record in local database with additional details
    
    Parameters:
    - request (CreateAdmin): An object containing admin details
    - db (Session): Database session
    
    Returns:
    - Dict containing admin details and registration status
    """
    auth_payload = {
        "name": f"{request.first_name} {request.last_name}",
        "email": request.email,
        "password1": request.password1.get_secret_value(),
        "password2": request.password2.get_secret_value(),
        "role": "admin" 
    }

    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                "http://localhost:8001/auth/register",
                json=auth_payload
            )
            auth_response.raise_for_status()
            auth_data = auth_response.json()
            print(auth_data)
            user_id = auth_data["id"]
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, 'response') else 500,
            detail=e.response.json() if hasattr(e, 'response') else str(e)
        )

    new_admin = Admin(
        id=user_id,
        first_name=request.first_name,
        last_name=request.last_name,
    )

    try:
        db.add(new_admin)
    except Exception as e:
        # If local admin creation fails, we should ideally delete the auth user
        # This would require an additional endpoint in the auth service
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"msg": f"Failed to create admin record: {str(e)}"}]
        )

    return {
        "id": user_id,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "email": request.email,
        "message": "Admin registration successful"
    }


@router.get("/protected")
async def protected_endpoint(user: dict = Depends(verify_admin)):
    return {"message": "You have access to this protected endpoint", "user": user}


@router.get("/me")
def me(user: dict = Depends(verify_token)):
    return {"message": "User authenticated", "user": user}
