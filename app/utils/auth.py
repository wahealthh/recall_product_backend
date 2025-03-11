from fastapi import Depends, HTTPException, status
import httpx
from typing import Optional
from app.utils.cookies import OAuth2PasswordBearerWithCookie

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="http://localhost:8001/auth/token")


async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify token with auth service"""
    try:
        async with httpx.AsyncClient() as client:
            # Send token in the expected format
            response = await client.post(
                "http://localhost:8001/auth/verify_token",
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
