from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import json

# Internal imports
try:
    from .database import engine, Base, get_db
    from .routes import auth_routes, fraud_routes
except ImportError:
    from database import engine, Base, get_db
    from routes import auth_routes, fraud_routes

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize Database
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database initialization error: {e}")

app = FastAPI(
    title="FraudEye Pro: Cybersecurity SaaS Platform",
    description="Advanced Financial Fraud Detection & Threat Response System",
    version="2.2.0"
)

# Attach Limiter to App
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(fraud_routes.router, prefix="/api/fraud", tags=["Fraud Engine"])

@app.get("/api/health")
@limiter.limit("5/minute")
def health_check(request: Request):
    return {
        "status": "online",
        "platform": "FraudEye Pro",
        "engine": "v2.2-Hardened",
        "database": "PostgreSQL Ready" if os.environ.get("DATABASE_URL") else "SQLite/Temp",
        "xai_module": "SHAP Integration Active"
    }
