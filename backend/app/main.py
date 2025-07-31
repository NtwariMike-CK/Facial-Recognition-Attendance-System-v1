# main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.database import engine, Base
from app.routers import auth, admin, employee
from app.middleware.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware




# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("FRAS Backend starting up...")
    yield
    # Shutdown
    print("FRAS Backend shutting down...")

app = FastAPI(
    title="FRAS - Facial Recognition Attendance System",
    description="Backend API for Facial Recognition Attendance System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(employee.router, prefix="/api/employee", tags=["Employee"])


@app.on_event("startup")
async def startup_event():
    print("Facial Recognition Attendance System started")

@app.on_event("shutdown")
async def shutdown_event():
    # Stop recognition service if running
    from app.services.recognition_service import recognition_service
    if recognition_service.is_running:
        recognition_service.stop_recognition()
    print("Application shutdown complete")
    

@app.get("/")
async def root():
    return {"message": "FRAS Backend API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "FRAS Backend is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)