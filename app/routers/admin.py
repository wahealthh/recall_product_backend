#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
import httpx

from app.config.config import settings
from app.engine.load import load
from app.models.admin import Admin
from app.models.practice import Practice
from app.schema.admin import CreateAdmin
from app.utils.auth import verify_admin, verify_token


router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    response: Response,
    request: CreateAdmin,
    http_request: Request,
    db: Session = Depends(load),
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
        "role": "admin",
    }

    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                "http://localhost:8001/auth/register", json=auth_payload
            )
            auth_response.raise_for_status()
            auth_data = auth_response.json()
            print(auth_data)
            user_id = auth_data["id"]
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if hasattr(e, "response") else 500,
            detail=e.response.json() if hasattr(e, "response") else str(e),
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
            detail=[{"msg": f"Failed to create admin record: {str(e)}"}],
        )

    return {
        "id": user_id,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "email": request.email,
        "message": "Admin registration successful",
        "access_token": auth_data["access_token"],
        "token_type": "bearer",
    }


@router.get("/protected")
async def protected_endpoint(user: dict = Depends(verify_admin)):
    return {"message": "You have access to this protected endpoint", "user": user}


@router.get("/me")
def me(
    user: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """
    Get authenticated admin's profile information including their associated practice.
    
    This endpoint returns the authenticated admin's details along with information
    about the practice they are associated with.
    
    Parameters:
    - user: Admin authentication data from the token verification
    - db: Database session
    
    Returns:
    - Admin details and associated practice information
    
    Raises:
    - 404 Not Found: If the admin or their practice is not found in the database
    """
    # Get admin from database
    admin = db.query_eng(Admin).filter(Admin.id == user["user_id"]).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found in database"
        )
    
    # Get practice associated with this admin
    practice = db.query_eng(Practice).filter(Practice.admin_id == admin.id).first()
    
    # Prepare response with admin and practice info
    response = {
        "message": "User authenticated",
        "user": user,
        "admin": {
            "id": admin.id,
            "first_name": admin.first_name,
            "last_name": admin.last_name,
            "created_at": admin.created_at,
            "updated_at": admin.updated_at
        }
    }
    
    # Add practice info if available
    if practice:
        response["practice"] = {
            "id": practice.id,
            "practice_name": practice.practice_name,
            "practice_email": practice.practice_email,
            "practice_phone_number": practice.practice_phone_number,
            "practice_address": practice.practice_address,
            "created_at": practice.created_at,
            "updated_at": practice.updated_at
        }
    else:
        response["practice"] = None
    
    return response
