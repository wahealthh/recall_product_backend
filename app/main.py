import fastapi
from app.routers import patient

app = fastapi.FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


app.include_router(patient.router)
