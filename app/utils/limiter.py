from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors that matches the frontend's expected format.
    """
    return JSONResponse(
        status_code=429,
        content={
            "message": "Rate limit exceeded",
            "error": "You can only make 3 requests per hour in demo mode. Please try again later",
            "retry_after": 3600  # 1 hour in seconds
        }
    ) 