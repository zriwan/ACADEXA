from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import Base, engine
from backend.routes.students import router as students_router
from backend.routes.teachers import router as teachers_router
from backend.routes.courses import router as courses_router
from backend.routes.enrollments import router as enrollments_router
from backend.routes.analytics import router as analytics_router




Base.metadata.create_all(bind=engine)

app = FastAPI(title="Acadexa Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students_router)
app.include_router(teachers_router)
app.include_router(courses_router)
app.include_router(enrollments_router)
app.include_router(analytics_router)

@app.get("/")
def root():
    return {"message": "Acadexa Backend Connected Successfully!"}
