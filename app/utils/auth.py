from fastapi import Depends, HTTPException, status
import httpx
from typing import Optional
from app.utils.cookies import OAuth2PasswordBearerWithCookie
from app.config.config import settings

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=f"{settings.AUTH_SERVICE_URL}{settings.AUTH_TOKEN_URL}")


async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify token with auth service"""
    try:
        async with httpx.AsyncClient() as client:
            # Send token in the expected format
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}{settings.AUTH_VERIFY_TOKEN_URL}",
                json={"token": token} 
            )

            print(response.json())
            if response.json().get("is_verified") == False:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User is not verified"
                )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

            return response.json() 

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to verify token: {str(e)}"
        )
    

async def verify_unverified_user(token: str = Depends(oauth2_scheme)):
    """
    Verify tokens from unverified users to grant limited access to specific endpoints.
    
    This function is designed to authenticate users who haven't completed the full
    verification process but need access to certain endpoints (like practice registration).
    It validates the token with the authentication service without requiring full
    verification status.
    
    The function:
    1. Takes the JWT token from the Authorization header
    2. Sends it to the auth service for validation
    3. Returns the user data if the token is valid
    
    Parameters:
    - token: JWT token extracted from the Authorization header
    
    Returns:
    - dict: User data from the authentication service (typically contains user_id and role)
    
    Raises:
    - 401 Unauthorized: If the token is invalid, expired, or the auth service rejects it
    - 401 Unauthorized: If there's a communication error with the auth service
    """
    try:
        async with httpx.AsyncClient() as client:
            # Send token in the expected format
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}{settings.AUTH_VERIFY_TOKEN_URL}",
                json={"token": token} 
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

            return response.json() 

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to verify token: {str(e)}"
        )

async def verify_admin(token: str = Depends(oauth2_scheme)):
    """Verify token and check if user is admin"""
    user_data = await verify_token(token)
    
    if user_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an admin"
        )
    
    return user_data
