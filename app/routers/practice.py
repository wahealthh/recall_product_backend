from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.engine.load import load
from app.models.practice import Practice
from app.models.admin import Admin
from app.schema.practice import CreatePractice, ShowPractice
from app.utils.auth import verify_admin

router = APIRouter(prefix="/practice", tags=["Practice Management"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ShowPractice)
async def create_practice(
    request: CreatePractice,
    user_data: dict = Depends(verify_admin),
    db: Session = Depends(load)
):
    """Create a new practice (admin only)"""
    # Get admin from database using auth service user_id
    print(user_data)
    
    # Check if practice with this email already exists
    existing_practice = db.query_eng(Practice).filter(Practice.practice_email == request.practice_email).first()
    if existing_practice:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Practice with email '{request.practice_email}' already exists"
        )
    
    admin = db.query_eng(Admin).filter(Admin.id == user_data["user_id"]).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found in database"
        )

    new_practice = Practice(
        practice_name=request.practice_name,
        practice_email=request.practice_email,
        practice_phone_number=request.practice_phone_number,
        practice_address=request.practice_address,
        admin_id=admin.id
    )

    try:
        db.add(new_practice)
        db.commit()
        db.refresh(new_practice)
        return new_practice
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create practice: {str(e)}"
        )
