from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, TransactionAudit
from pydantic import BaseModel
import pickle
import os
import numpy as np
from datetime import datetime

router = APIRouter()

# Schema
class TransactionData(BaseModel):
    step: int
    type: str
    amount: float
    old_balance_sender: float
    new_balance_sender: float
    old_balance_receiver: float
    new_balance_receiver: float

# Load ML Model (using the lite version for SaaS stability)
MODEL_PATH = "ml_models/random_forest_baseline.pkl"
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
except:
    model = None

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(TransactionAudit).count()
    fraud = db.query(TransactionAudit).filter(TransactionAudit.prediction == "FRAUD").count()
    recent = db.query(TransactionAudit).order_by(TransactionAudit.timestamp.desc()).limit(10).all()
    
    return {
        "total_scanned": total,
        "fraud_alerts": fraud,
        "risk_index": round((fraud/total * 100), 2) if total > 0 else 0,
        "recent_activity": recent
    }

@router.post("/predict")
async def predict_fraud(data: TransactionData, db: Session = Depends(get_db)):
    if not model:
        raise HTTPException(status_code=500, detail="ML Model offline")
    
    # Feature Engineering
    features = np.array([[
        1 if data.type == "TRANSFER" else 0,
        data.amount,
        data.old_balance_sender,
        data.new_balance_sender,
        data.old_balance_receiver,
        data.new_balance_receiver
    ]])
    
    prob = float(model.predict_proba(features)[0][1])
    prediction = "FRAUD" if prob > 0.5 else "NOT FRAUD"
    
    # Audit Logging
    audit = TransactionAudit(
        transaction_id=f"TXN-{os.urandom(4).hex().upper()}",
        amount=data.amount,
        prediction=prediction,
        risk_score=prob
    )
    db.add(audit)
    db.commit()
    
    return {
        "transaction_id": audit.transaction_id,
        "prediction": prediction,
        "probability": prob,
        "risk_level": "CRITICAL" if prob > 0.8 else "HIGH" if prob > 0.5 else "LOW",
        "timestamp": datetime.now().isoformat()
    }
