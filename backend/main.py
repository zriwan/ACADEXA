# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.database import Base, engine

from backend.routes.students import router as students_router
from backend.routes.teachers import router as teachers_router
from backend.routes.courses import router as courses_router
from backend.routes.enrollments import router as enrollments_router
from backend.routes.analytics import router as analytics_router
from backend.routes.auth import router as auth_router

app = FastAPI(title="Acadexa Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ DB work happens on startup — won’t hang imports
@app.on_event("startup")
def startup_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        print("✅ DB connected and metadata ensured")
    except Exception as e:
        print(f"❌ DB connection failed on startup: {e}")

# Routers
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(teachers_router)
app.include_router(courses_router)
app.include_router(enrollments_router)
app.include_router(analytics_router)

@app.get("/")
def root():
    return {"message": "Acadexa Backend Connected Successfully!"}
