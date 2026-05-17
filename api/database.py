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
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    if os.environ.get("VERCEL"):
        SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/fraudeye_pro.db"
    else:
        SQLALCHEMY_DATABASE_URL = "sqlite:///./fraudeye_pro.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    status = Column(String, default="ACTIVE") # ACTIVE, FROZEN, FLAGGED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TransactionAudit(Base):
    __tablename__ = "transaction_audit"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String)
    amount = Column(Float)
    prediction = Column(String)
    risk_score = Column(Float)
    explanation = Column(String)
    status = Column(String, default="PENDING") # PENDING, REVIEWED, BLOCKED, CLEARED
    admin_action = Column(String, nullable=True) # Description of action taken
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
