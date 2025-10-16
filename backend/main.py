# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import Base, engine
from backend.routes.students import router as students_router  # ← import the submodule directly

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Acadexa Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students_router)

@app.get("/")
def root():
    return {"message": "Acadexa Backend Connected Successfully!"}
