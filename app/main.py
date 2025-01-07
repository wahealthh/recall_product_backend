import fastapi
from fastapi.middleware.cors import CORSMiddleware
from app.routers import patient
from app.routers import mail

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://wahealth.co.uk",
        "https://www.wahealth.co.uk",
        "http://localhost:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5502",
        "http://localhost:5174",
        "http://localhost:5173",
        "https://wa-health-pwa.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


app.include_router(patient.router)
app.include_router(mail.router)
