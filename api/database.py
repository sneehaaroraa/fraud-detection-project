from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime
import os

# Production DB: PostgreSQL (e.g., Supabase, RDS)
# Local/Vercel Fallback: SQLite
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Fix for SQLAlchemy/PostgreSQL compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    # Fallback to local SQLite /tmp for Vercel
    if os.environ.get("VERCEL"):
        SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/fraudeye_pro.db"
    else:
        SQLALCHEMY_DATABASE_URL = "sqlite:///./fraudeye_pro.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Transaction Audit with Explainability
class TransactionAudit(Base):
    __tablename__ = "transaction_audit"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String)
    amount = Column(Float)
    prediction = Column(String)
    risk_score = Column(Float)
    explanation = Column(String) # JSON string of SHAP-based reasons
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
