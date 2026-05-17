from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

# Internal imports
from .database import engine, Base, get_db
from .routes import auth_routes, fraud_routes

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FraudEye Pro: Cybersecurity SaaS Platform",
    description="Advanced Financial Fraud Detection & Threat Response System",
    version="2.0.0"
)

# CORS Configuration for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(fraud_routes.router, prefix="/api/fraud", tags=["Fraud Engine"])

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "platform": "FraudEye Pro",
        "engine": "v2.0-Hybrid-ML"
    }
