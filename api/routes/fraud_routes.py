from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db, TransactionAudit
from pydantic import BaseModel
import pickle
import os
import numpy as np
import json
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
FEATURES_PATH = os.path.join(BASE_DIR, "ml_models", "feature_list.pkl")

model = None
feature_list = None
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(FEATURES_PATH, "rb") as f:
        feature_list = pickle.load(f)
except Exception as e:
    print(f"Error loading model assets: {e}")

def get_xai_explanation(features_array):
    """
    Simulated XAI logic using heuristic 'feature importance'.
    In a full SHAP implementation, we would use:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(features_array)
    """
    reasons = []
    # Simplified XAI based on top weights
    if features_array[0][1] > 200000:
        reasons.append("Extreme Transaction Amount")
    if features_array[0][3] == 0:
        reasons.append("Account Liquidation (Drained)")
    if features_array[0][0] == 1: # TRANSFER
        reasons.append("High-Risk Transaction Type (TRANSFER)")
    if features_array[0][2] == 0:
        reasons.append("Transaction from Empty Account")
        
    return json.dumps(reasons if reasons else ["Standard Pattern"])

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
    # Feature Engineering (Mapping to exact model expectation)
    features = np.array([[
        1 if data.type == "TRANSFER" else 0,
        data.amount,
        data.old_balance_sender,
        data.new_balance_sender,
        data.old_balance_receiver,
        data.new_balance_receiver
    ]])
    
    if model:
        prob = float(model.predict_proba(features)[0][1])
        prediction = "FRAUD" if prob > 0.5 else "NOT FRAUD"
        explanation = get_xai_explanation(features)
    else:
        prob = 0.85 if (data.type == "TRANSFER" and data.amount > 200000) else 0.1
        prediction = "FRAUD" if prob > 0.5 else "NOT FRAUD"
        explanation = json.dumps(["Model Offline - Rule Based Fallback"])
    
    # Audit Logging
    audit = TransactionAudit(
        transaction_id=f"TXN-{os.urandom(4).hex().upper()}",
        amount=data.amount,
        prediction=prediction,
        risk_score=prob,
        explanation=explanation
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    
    return {
        "transaction_id": audit.transaction_id,
        "prediction": prediction,
        "probability": prob,
        "risk_level": "CRITICAL" if prob > 0.8 else "HIGH" if prob > 0.5 else "LOW",
        "explanation": json.loads(explanation),
        "timestamp": datetime.now().isoformat()
    }
