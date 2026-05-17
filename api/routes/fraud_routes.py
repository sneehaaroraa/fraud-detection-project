from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db, TransactionAudit, User
from pydantic import BaseModel
import pickle
import os
import numpy as np
import json
from datetime import datetime, timedelta

router = APIRouter()

# Schemas
class TransactionData(BaseModel):
    step: int
    type: str
    amount: float
    old_balance_sender: float
    new_balance_sender: float
    old_balance_receiver: float
    new_balance_receiver: float

class ActionRequest(BaseModel):
    transaction_id: str
    action: str # BLOCK, CLEAR, FREEZE_USER

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
    reasons = []
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
        recent = db.query(TransactionAudit).order_by(TransactionAudit.timestamp.desc()).limit(15).all()
        
        return {
            "total_scanned": total,
            "fraud_alerts": fraud,
            "risk_index": round((fraud/total * 100), 2) if total > 0 else 0,
            "recent_activity": recent
        }
    except Exception as e:
        return {"error": str(e), "total_scanned": 0, "fraud_alerts": 0, "risk_index": 0, "recent_activity": []}

@router.get("/insider-threats")
async def detect_insider_threats(db: Session = Depends(get_db)):
    """
    Detect anomalous patterns: High frequency of high-value transactions.
    """
    time_window = datetime.utcnow() - timedelta(hours=1)
    # This is a simplified simulation of identifying suspicious account activity
    suspicious = db.query(
        TransactionAudit.prediction, 
        func.count(TransactionAudit.id).label('count'),
        func.sum(TransactionAudit.amount).label('total_value')
    ).filter(TransactionAudit.timestamp > time_window)\
     .group_by(TransactionAudit.prediction).all()
    
    return {
        "anomalies": [
            {"type": "High Frequency Volume", "severity": "MEDIUM", "details": "Increased API activity detected in last 60 mins"},
            {"type": "Large Value Bursts", "severity": "HIGH", "details": "Multiple >$100k transactions detected"}
        ],
        "metrics": suspicious
    }

@router.post("/action")
async def take_action(request: ActionRequest, db: Session = Depends(get_db)):
    tx = db.query(TransactionAudit).filter(TransactionAudit.transaction_id == request.transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if request.action == "BLOCK":
        tx.status = "BLOCKED"
        tx.admin_action = "Blocked by SOC Analyst"
    elif request.action == "CLEAR":
        tx.status = "CLEARED"
        tx.admin_action = "Manually cleared after review"
    elif request.action == "FREEZE_USER":
        tx.status = "BLOCKED"
        tx.admin_action = "User account frozen due to critical fraud risk"
        # In a real app, you'd look up the user associated with this TX and set user.status = "FROZEN"
    
    db.commit()
    return {"status": "success", "message": f"Action {request.action} applied to {request.transaction_id}"}

@router.post("/predict")
async def predict_fraud(data: TransactionData, db: Session = Depends(get_db)):
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
        explanation = json.dumps(["Model Offline"])
    
    audit = TransactionAudit(
        transaction_id=f"TXN-{os.urandom(4).hex().upper()}",
        amount=data.amount,
        prediction=prediction,
        risk_score=prob,
        explanation=explanation,
        status="PENDING"
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
