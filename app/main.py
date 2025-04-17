import fastapi
from fastapi.middleware.cors import CORSMiddleware
from app.routers import patient
from app.routers import mail
from app.routers import admin
from app.routers import practice
from app.routers import recall
from slowapi.errors import RateLimitExceeded
from app.utils.limiter import limiter, custom_rate_limit_exceeded_handler
from app.config.config import settings

app = fastapi.FastAPI(title=settings.project_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
app.include_router(recall.router)
