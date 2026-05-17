# =============================================================
# VERCEL DEPLOYMENT: FRAUD DETECTION REST API (FastAPI)
# =============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import numpy as np
from datetime import datetime
import os

app = FastAPI(
    title="🛡️ FraudEye API",
    description="Real-time Fraud Detection Service (Optimized for Vercel)",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load Model ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# Prefer Random Forest for Vercel stability (smaller memory footprint)
MODEL_PATH = os.path.join(BASE_DIR, "models", "random_forest_baseline.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "models", "label_encoder.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "models", "feature_list.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(FEATURES_PATH, "rb") as f:
        feature_list = pickle.load(f)
    print("✅ Optimized model loaded successfully!")
except Exception as e:
    print(f"⚠️  Model load failed: {e}")
    model = None
    feature_list = None

# ── Schemas ───────────────────────────────────────────────────
class TransactionInput(BaseModel):
    step: int
    type: str
    amount: float
    old_balance_sender: float
    new_balance_sender: float
    old_balance_receiver: float
    new_balance_receiver: float
    isFlaggedFraud: int = 0

class FraudPredictionResponse(BaseModel):
    transaction_id: str
    timestamp: str
    prediction: str
    fraud_probability: float
    risk_level: str
    rules_triggered: list
    model_used: str
    processing_time_ms: float

# ── Logic ─────────────────────────────────────────────────────
def check_rules(tx: TransactionInput) -> list:
    triggered = []
    tx_type = tx.type.upper()
    if tx_type == 'TRANSFER' and tx.amount > 100_000:
        triggered.append("RULE_001: High-Value TRANSFER")
    if tx_type == 'CASH_OUT' and tx.amount > 200_000:
        triggered.append("RULE_002: High-Value CASH_OUT")
    if tx.new_balance_sender == 0 and tx.amount > 50_000:
        triggered.append("RULE_003: Account Drained")
    if tx.amount > 500_000:
        triggered.append("RULE_005: Large Amount")
    return triggered

def engineer_features(tx: TransactionInput):
    type_map = {'CASH_IN': 0, 'CASH_OUT': 1, 'DEBIT': 2, 'PAYMENT': 3, 'TRANSFER': 4}
    tx_type = tx.type.upper()
    type_encoded = type_map.get(tx_type, 0)

    # Creating a dictionary and then converting to list in the correct order
    features = {
        'type_encoded': type_encoded,
        'amount': tx.amount,
        'old_balance_sender': tx.old_balance_sender,
        'new_balance_sender': tx.new_balance_sender,
        'old_balance_receiver': tx.old_balance_receiver,
        'new_balance_receiver': tx.new_balance_receiver,
        'balance_diff_sender': tx.old_balance_sender - tx.new_balance_sender,
        'balance_diff_receiver': tx.new_balance_receiver - tx.old_balance_receiver,
        'account_drained': 1 if tx.new_balance_sender == 0 else 0,
        'zero_start_balance': 1 if tx.old_balance_sender == 0 else 0,
        'amount_to_balance_ratio': (tx.amount / tx.old_balance_sender if tx.old_balance_sender > 0 else 0),
        'hour_of_day': tx.step % 24,
        'is_transfer_or_cashout': 1 if tx_type in ['TRANSFER', 'CASH_OUT'] else 0,
        'isFlaggedFraud': tx.isFlaggedFraud,
    }

    # Ensure features are in the exact order the model expects
    if feature_list:
        return np.array([[features[f] for f in feature_list]])
    else:
        # Fallback order if feature_list is missing
        return np.array([[features[k] for k in sorted(features.keys())]])

# ── Endpoints ─────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": model is not None, "optimized": True}

@app.post("/api/predict", response_model=FraudPredictionResponse)
def predict(transaction: TransactionInput):
    import time
    start = time.time()
    
    rules_triggered = check_rules(transaction)
    
    if model is not None:
        try:
            X = engineer_features(transaction)
            # Some sklearn models only have predict, check for predict_proba
            if hasattr(model, 'predict_proba'):
                fraud_prob = float(model.predict_proba(X)[0][1])
            else:
                fraud_prob = float(model.predict(X)[0])
            
            prediction = "FRAUD" if fraud_prob >= 0.5 else "NOT FRAUD"
            model_name = "RandomForest (Lite)"
        except Exception as e:
            print(f"Prediction error: {e}")
            fraud_prob = 0.5 if len(rules_triggered) > 0 else 0.1
            prediction = "FRAUD" if fraud_prob >= 0.5 else "NOT FRAUD"
            model_name = "Fallback Heuristic"
    else:
        fraud_prob = 0.85 if len(rules_triggered) >= 2 else 0.15
        prediction = "FRAUD" if fraud_prob >= 0.5 else "NOT FRAUD"
        model_name = "Rule-Based Engine"

    risk_level = "CRITICAL" if fraud_prob >= 0.8 else "HIGH" if fraud_prob >= 0.5 else "MEDIUM" if fraud_prob >= 0.3 else "LOW"
    
    return {
        "transaction_id": f"TX_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction,
        "fraud_probability": round(fraud_prob, 4),
        "risk_level": risk_level,
        "rules_triggered": rules_triggered if rules_triggered else ["None"],
        "model_used": model_name,
        "processing_time_ms": round((time.time() - start) * 1000, 2),
    }
