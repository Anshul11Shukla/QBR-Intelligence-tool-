from app.api.qa_coach import router as qa_coach_router
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.cases import router as cases_router
from app.api.uploads import router as uploads_router
from app.api.analytics import router as analytics_router
from app.api.evidence import router as evidence_router
from app.database import initialize_database
from app.api.exports import router as exports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="QBR Intelligence Studio API",
    description="QBR analytics, evidence and AI agents",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")
app.include_router(
    qa_coach_router,
    prefix="/api",
)
app.include_router(exports_router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "QBR Intelligence Studio API is running",
        "version": "0.4.0",
    }
