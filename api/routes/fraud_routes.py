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

# Load ML Model using absolute path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "random_forest_baseline.pkl")

model = None
try:
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    else:
        print(f"Model file not found at {MODEL_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    try:
        total = db.query(TransactionAudit).count()
        fraud = db.query(TransactionAudit).filter(TransactionAudit.prediction == "FRAUD").count()
        recent = db.query(TransactionAudit).order_by(TransactionAudit.timestamp.desc()).limit(10).all()
        
        return {
            "total_scanned": total,
            "fraud_alerts": fraud,
            "risk_index": round((fraud/total * 100), 2) if total > 0 else 0,
            "recent_activity": recent
        }
    except Exception as e:
        return {"error": str(e), "total_scanned": 0, "fraud_alerts": 0, "risk_index": 0, "recent_activity": []}

@router.post("/predict")
async def predict_fraud(data: TransactionData, db: Session = Depends(get_db)):
    # Feature Engineering
    features = np.array([[
        1 if data.type == "TRANSFER" else 0,
        data.amount,
        data.old_balance_sender,
        data.new_balance_sender,
        data.old_balance_receiver,
        data.new_balance_receiver
    ]])
    
    if model:
        try:
            prob = float(model.predict_proba(features)[0][1])
            prediction = "FRAUD" if prob > 0.5 else "NOT FRAUD"
        except Exception as e:
            print(f"Model prediction error: {e}")
            prob = 0.5 if data.amount > 100000 else 0.1
            prediction = "FRAUD" if prob > 0.5 else "NOT FRAUD"
    else:
        # Fallback heuristic if model is offline
        prob = 0.85 if (data.type == "TRANSFER" and data.amount > 200000) else 0.1
        prediction = "FRAUD" if prob > 0.5 else "NOT FRAUD"
    
    # Audit Logging
    try:
        audit = TransactionAudit(
            transaction_id=f"TXN-{os.urandom(4).hex().upper()}",
            amount=data.amount,
            prediction=prediction,
            risk_score=prob
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        
        return {
            "transaction_id": audit.transaction_id,
            "prediction": prediction,
            "probability": prob,
            "risk_level": "CRITICAL" if prob > 0.8 else "HIGH" if prob > 0.5 else "LOW",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
