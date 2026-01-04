# backend/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.database import Base, engine
from backend.routes.auth import router as auth_router
from backend.routes.courses import router as courses_router
from backend.routes.enrollments import router as enrollments_router
from backend.routes.students import router as students_router
from backend.routes.teachers import router as teachers_router
from backend.routes.analytics import router as analytics_router

from backend.routes.voice import router as voice_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== STARTUP =====
    try:
        # Quick DB connectivity check
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        print("✅ DB connected and metadata ensured")
    except Exception as e:
        print(f"❌ DB connection failed on startup: {e}")

    yield

    # ===== SHUTDOWN =====
    # If you keep pooled engines or external clients, close them here.
    # (SQLAlchemy 2.x engine disposes automatically when GC'd, but you can force:)
    try:
        engine.dispose()
        print("🧹 DB engine disposed")
    except Exception as e:
        print(f"⚠️ DB engine dispose error: {e}")


app = FastAPI(title="Acadexa Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(teachers_router)
app.include_router(courses_router)
app.include_router(enrollments_router)
app.include_router(analytics_router)


app.include_router(voice_router)







@app.get("/")
def root():
    return {"message": "Acadexa Backend Connected Successfully!"}
