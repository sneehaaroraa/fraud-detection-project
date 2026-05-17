# =============================================================
# WEEK 6: FRAUD DETECTION REST API (FastAPI)
# =============================================================
# 📌 What this file does:
#   - Loads the trained model from Week 5
#   - Creates a REST API that accepts transaction data
#   - Returns fraud prediction + probability score
#   - Logs all requests for monitoring
#
# ▶️ How to run:
#   python3 week6_api.py
#
# ▶️ Then open your browser:
#   http://localhost:8000/docs  ← Interactive API documentation
# =============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import json
import os
import socket
import uvicorn

os.makedirs("week6/logs", exist_ok=True)

API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "8000"))


def find_available_port(host: str, start_port: int, attempts: int = 20) -> int:
    """Find a local port for the API, starting at API_PORT."""
    for port in range(start_port, start_port + attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((host, port))
            return port
        except PermissionError as exc:
            raise RuntimeError(
                "This terminal/environment blocked local server startup."
            ) from exc
        except OSError:
            continue

    raise RuntimeError(
        f"Could not find an available port from {start_port} to "
        f"{start_port + attempts - 1}."
    )

# ── Load Model ────────────────────────────────────────────────
print("📦 Loading fraud detection model...")

try:
    with open("week5/models/best_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open("week5/models/label_encoder.pkl", "rb") as f:
        label_encoder = pickle.load(f)
    with open("week5/models/feature_list.pkl", "rb") as f:
        feature_list = pickle.load(f)
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    print("⚠️  Model not found. Run week5_advanced_models.py first.")
    print("   Running in DEMO mode with mock predictions.")
    model = None
    label_encoder = None
    feature_list = None

# ── FastAPI App Setup ─────────────────────────────────────────
app = FastAPI(
    title="🛡️ Fraud Detection API",
    description="""
## Threat Response in Digital Transactions
### Week 6 — Model Deployment

This API accepts financial transaction data and returns:
- **Fraud prediction** (Fraud / Not Fraud)
- **Probability score** (0.0 to 1.0)
- **Risk level** (LOW / MEDIUM / HIGH / CRITICAL)
- **Triggered rules** from Week 3

**Dataset:** PaySim Mobile Money Transactions  
**Model:** Best performing model from Week 5 (XGBoost / LightGBM)
    """,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Schemas ──────────────────────────────────
class TransactionInput(BaseModel):
    """
    Input: one financial transaction to be checked for fraud.
    All fields match the PaySim dataset columns.
    """
    step: int = Field(..., examples=[1], description="Hour number (1-744)")
    type: str = Field(..., examples=["TRANSFER"],
                      description="Transaction type: CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER")
    amount: float = Field(..., examples=[181000.0], description="Transaction amount in currency")
    old_balance_sender: float = Field(..., examples=[181000.0], description="Sender balance before tx")
    new_balance_sender: float = Field(..., examples=[0.0], description="Sender balance after tx")
    old_balance_receiver: float = Field(..., examples=[0.0], description="Receiver balance before tx")
    new_balance_receiver: float = Field(..., examples=[0.0], description="Receiver balance after tx")
    isFlaggedFraud: int = Field(default=0, examples=[0], description="Bank internal flag (0 or 1)")

class FraudPredictionResponse(BaseModel):
    """Output: fraud prediction result"""
    transaction_id: str
    timestamp: str
    prediction: str           # "FRAUD" or "NOT FRAUD"
    fraud_probability: float  # 0.0 to 1.0
    risk_level: str           # LOW / MEDIUM / HIGH / CRITICAL
    rules_triggered: list     # Which Week 3 rules fired
    model_used: str
    processing_time_ms: float

# ── Monitoring Stats ──────────────────────────────────────────
stats = {
    "total_requests": 0,
    "fraud_detected": 0,
    "not_fraud": 0,
    "start_time": datetime.now().isoformat()
}

# ── Helper Functions ──────────────────────────────────────────
def engineer_features(tx: TransactionInput) -> pd.DataFrame:
    """Convert raw transaction into model features (same as Week 4/5)"""

    # Encode transaction type
    type_map = {'CASH_IN': 0, 'CASH_OUT': 1, 'DEBIT': 2, 'PAYMENT': 3, 'TRANSFER': 4}
    tx_type = tx.type.upper()
    if label_encoder is not None and tx_type in label_encoder.classes_:
        type_encoded = int(label_encoder.transform([tx_type])[0])
    else:
        type_encoded = type_map.get(tx_type, 0)

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
        'amount_to_balance_ratio': (tx.amount / tx.old_balance_sender
                                    if tx.old_balance_sender > 0 else 0),
        'hour_of_day': tx.step % 24,
        'is_transfer_or_cashout': 1 if tx_type in ['TRANSFER', 'CASH_OUT'] else 0,
        'isFlaggedFraud': tx.isFlaggedFraud,
    }

    X = pd.DataFrame([features])
    if feature_list is not None:
        X = X[feature_list]
    return X

def check_rules(tx: TransactionInput) -> list:
    """Apply the 7 fraud rules from Week 3"""
    triggered = []
    if tx.type.upper() == 'TRANSFER' and tx.amount > 100_000:
        triggered.append("RULE_001: High-Value TRANSFER")
    if tx.type.upper() == 'CASH_OUT' and tx.amount > 200_000:
        triggered.append("RULE_002: High-Value CASH_OUT")
    if tx.new_balance_sender == 0 and tx.amount > 50_000:
        triggered.append("RULE_003: Account Completely Drained")
    if tx.isFlaggedFraud == 1:
        triggered.append("RULE_004: Bank Internal Flag")
    if tx.amount > 500_000:
        triggered.append("RULE_005: Very Large Amount")
    if tx.old_balance_sender == 0 and tx.amount > 0:
        triggered.append("RULE_007: Zero-Balance Origin Account")
    return triggered

def get_risk_level(probability: float) -> str:
    if probability >= 0.8:   return "CRITICAL"
    elif probability >= 0.5: return "HIGH"
    elif probability >= 0.3: return "MEDIUM"
    else:                    return "LOW"

def log_request(tx_id: str, tx: TransactionInput, result: dict):
    """Save each API call to a log file for monitoring"""
    log_entry = {
        "transaction_id": tx_id,
        "timestamp": datetime.now().isoformat(),
        "input": tx.model_dump(),
        "result": result,
    }
    log_file = f"week6/logs/api_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

# ── API Endpoints ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check — confirms API is running"""
    return {
        "status": "running ✅",
        "service": "Fraud Detection API",
        "version": "1.0.0",
        "model_loaded": model is not None,
        "docs": "Visit /docs for interactive API documentation"
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check with stats"""
    return {
        "status": "healthy",
        "uptime_since": stats["start_time"],
        "total_requests": stats["total_requests"],
        "fraud_detected": stats["fraud_detected"],
        "not_fraud": stats["not_fraud"],
        "fraud_rate": (f"{stats['fraud_detected']/stats['total_requests']*100:.2f}%"
                       if stats["total_requests"] > 0 else "N/A"),
        "model_loaded": model is not None,
    }

@app.post("/predict", response_model=FraudPredictionResponse, tags=["Prediction"])
def predict_fraud(transaction: TransactionInput):
    """
    **Main endpoint** — Submit a transaction, get a fraud prediction.
    
    Returns fraud probability, risk level, and which rules were triggered.
    """
    import time
    start = time.time()

    # Generate transaction ID
    tx_id = f"TX_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    # Apply rule-based checks
    rules_triggered = check_rules(transaction)

    # ML model prediction
    if model is not None:
        X = engineer_features(transaction)
        fraud_prob = float(model.predict_proba(X)[0][1])
        prediction = "FRAUD" if fraud_prob >= 0.5 else "NOT FRAUD"
        model_name = type(model).__name__
    else:
        # Demo mode: use rules as fallback
        fraud_prob = 0.85 if len(rules_triggered) >= 2 else 0.15
        prediction = "FRAUD" if fraud_prob >= 0.5 else "NOT FRAUD"
        model_name = "Rule-Based (Demo Mode — run Week 5 first)"

    risk_level = get_risk_level(fraud_prob)
    processing_ms = (time.time() - start) * 1000

    # Update monitoring stats
    stats["total_requests"] += 1
    if prediction == "FRAUD":
        stats["fraud_detected"] += 1
    else:
        stats["not_fraud"] += 1

    result = {
        "transaction_id": tx_id,
        "timestamp": datetime.now().isoformat(),
        "prediction": prediction,
        "fraud_probability": round(fraud_prob, 4),
        "risk_level": risk_level,
        "rules_triggered": rules_triggered if rules_triggered else ["No rules triggered"],
        "model_used": model_name,
        "processing_time_ms": round(processing_ms, 2),
    }

    log_request(tx_id, transaction, result)
    return result

@app.post("/predict/batch", tags=["Prediction"])
def predict_batch(transactions: list[TransactionInput]):
    """Submit multiple transactions at once (max 100)"""
    if len(transactions) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 transactions per batch")
    return [predict_fraud(tx) for tx in transactions]

@app.get("/stats", tags=["Monitoring"])
def get_stats():
    """View API monitoring statistics"""
    return stats

# ── Run Server ────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        run_port = find_available_port(API_HOST, API_PORT)
    except RuntimeError as exc:
        print(f"\n❌ {exc}")
        if "blocked local server startup" in str(exc):
            print("Run the API from VS Code Terminal or macOS Terminal:")
            print("   python3 week6_api.py")
        else:
            print("Close the existing API terminal or set a different port, for example:")
            print("   API_PORT=8010 python3 week6_api.py")
        raise SystemExit(1)

    if run_port != API_PORT:
        print(f"⚠️  Port {API_PORT} is busy. Using port {run_port} instead.")

    print("\n" + "="*60)
    print("🚀 STARTING FRAUD DETECTION API")
    print("="*60)
    print(f"  URL:  http://{API_HOST}:{run_port}")
    print(f"  Docs: http://{API_HOST}:{run_port}/docs  ← Open this in browser!")
    print("  Stop: Press Ctrl+C")
    print("="*60 + "\n")

    try:
        uvicorn.run(app, host=API_HOST, port=run_port, reload=False)
    except PermissionError:
        print("\n❌ Your current terminal/environment is blocking local server startup.")
        print("Try running this file directly in VS Code Terminal or macOS Terminal:")
        print("   python3 week6_api.py")
        raise SystemExit(1)
