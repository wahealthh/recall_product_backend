import fastapi
from fastapi.middleware.cors import CORSMiddleware
from app.routers import patient
from app.routers import mail
from app.routers import admin
from app.routers import practice
from slowapi.errors import RateLimitExceeded
from app.utils.limiter import limiter, custom_rate_limit_exceeded_handler

app = fastapi.FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://wahealth.co.uk",
        "https://www.wahealth.co.uk",
        "http://localhost:5174",
        "http://localhost:5173",
        "https://wa-health-pwa.onrender.com",
        "http://localhost:8001",
        "https://app.wahealth.co.uk",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/test-rate-limit")
@limiter.limit("1/hour")
async def test_rate_limit(request: fastapi.Request):
    return {"message": "Hello, World!"}


app.include_router(patient.router)
app.include_router(mail.router)
app.include_router(admin.router)
app.include_router(practice.router)
