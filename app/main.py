import fastapi
from app.routers import patient
from app.routers import mail

app = fastapi.FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


app.include_router(patient.router)
app.include_router(mail.router)
