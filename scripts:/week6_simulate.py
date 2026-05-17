# =============================================================
# WEEK 6: REAL-TIME TRANSACTION SIMULATION SCRIPT
# =============================================================
# 📌 What this does:
#   Simulates a stream of financial transactions being sent
#   to your fraud detection API in real time, one by one.
#   Shows live predictions in the terminal.
#
# ▶️ How to run:
#   1. First start the API:  python3 week6_api.py
#   2. In a NEW terminal:    python3 week6_simulate.py
# =============================================================

import requests
import random
import time
import json
from datetime import datetime

API_URL = "http://localhost:8000/predict"

# ── Transaction Templates ─────────────────────────────────────
# Mix of fraud and legit transactions to simulate real traffic

TRANSACTION_TEMPLATES = [
    # HIGH RISK — likely fraud
    {"step": 1, "type": "TRANSFER", "amount": 450000, "old_balance_sender": 450000,
     "new_balance_sender": 0, "old_balance_receiver": 0, "new_balance_receiver": 0,
     "isFlaggedFraud": 0, "label": "🚨 LIKELY FRAUD"},

    {"step": 5, "type": "CASH_OUT", "amount": 250000, "old_balance_sender": 250000,
     "new_balance_sender": 0, "old_balance_receiver": 100000, "new_balance_receiver": 350000,
     "isFlaggedFraud": 0, "label": "🚨 LIKELY FRAUD"},

    {"step": 10, "type": "TRANSFER", "amount": 1200000, "old_balance_sender": 1200000,
     "new_balance_sender": 0, "old_balance_receiver": 0, "new_balance_receiver": 1200000,
     "isFlaggedFraud": 1, "label": "🚨 LIKELY FRAUD"},

    # LOW RISK — likely legit
    {"step": 2, "type": "PAYMENT", "amount": 1500, "old_balance_sender": 50000,
     "new_balance_sender": 48500, "old_balance_receiver": 10000, "new_balance_receiver": 11500,
     "isFlaggedFraud": 0, "label": "✅ LIKELY LEGIT"},

    {"step": 3, "type": "CASH_IN", "amount": 5000, "old_balance_sender": 0,
     "new_balance_sender": 5000, "old_balance_receiver": 50000, "new_balance_receiver": 55000,
     "isFlaggedFraud": 0, "label": "✅ LIKELY LEGIT"},

    {"step": 7, "type": "TRANSFER", "amount": 2000, "old_balance_sender": 25000,
     "new_balance_sender": 23000, "old_balance_receiver": 5000, "new_balance_receiver": 7000,
     "isFlaggedFraud": 0, "label": "✅ LIKELY LEGIT"},

    # MEDIUM RISK — borderline
    {"step": 4, "type": "CASH_OUT", "amount": 95000, "old_balance_sender": 100000,
     "new_balance_sender": 5000, "old_balance_receiver": 0, "new_balance_receiver": 95000,
     "isFlaggedFraud": 0, "label": "⚠️  BORDERLINE"},

    {"step": 6, "type": "TRANSFER", "amount": 180000, "old_balance_sender": 200000,
     "new_balance_sender": 20000, "old_balance_receiver": 50000, "new_balance_receiver": 230000,
     "isFlaggedFraud": 0, "label": "⚠️  BORDERLINE"},
]

# ── Run Simulation ────────────────────────────────────────────
def run_simulation(n_transactions: int = 20, delay_seconds: float = 1.5):
    print("="*65)
    print("🏦 FRAUD DETECTION API — REAL-TIME TRANSACTION SIMULATION")
    print("="*65)
    print(f"  Sending {n_transactions} transactions to: {API_URL}")
    print(f"  Interval: {delay_seconds}s between transactions")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*65)
    print(f"\n  {'#':<4} {'Expected':<18} {'Prediction':<12} {'Prob':>6} {'Risk':<10} {'Rules Triggered'}")
    print("  " + "-"*80)

    fraud_count = 0
    errors = 0

    for i in range(n_transactions):
        # Pick a random transaction (weighted toward legit, like real life)
        template = random.choice(TRANSACTION_TEMPLATES)
        expected_label = template.pop("label", "Unknown")

        # Add small random variation to amounts
        tx_data = template.copy()
        tx_data["amount"] = tx_data["amount"] * random.uniform(0.9, 1.1)

        try:
            response = requests.post(API_URL, json=tx_data, timeout=5)

            if response.status_code == 200:
                result = response.json()
                pred = result["prediction"]
                prob = result["fraud_probability"]
                risk = result["risk_level"]
                rules = result["rules_triggered"]
                rules_str = rules[0] if rules else "None"

                if pred == "FRAUD":
                    fraud_count += 1

                print(f"  {i+1:<4} {expected_label:<18} {pred:<12} {prob:>6.3f} {risk:<10} {rules_str[:35]}")

            else:
                print(f"  {i+1:<4} ❌ API Error: {response.status_code}")
                errors += 1

        except requests.ConnectionError:
            print(f"\n  ❌ Cannot connect to API at {API_URL}")
            print("  Make sure week6_api.py is running first!")
            return
        except Exception as e:
            print(f"  {i+1:<4} ❌ Error: {e}")
            errors += 1

        template["label"] = expected_label  # Restore for next iteration
        time.sleep(delay_seconds)

    # Summary
    print("\n" + "="*65)
    print("📊 SIMULATION COMPLETE")
    print("="*65)
    print(f"  Total transactions sent: {n_transactions}")
    print(f"  Fraud detected:          {fraud_count} ({fraud_count/n_transactions*100:.1f}%)")
    print(f"  Not fraud:               {n_transactions - fraud_count - errors}")
    print(f"  Errors:                  {errors}")
    print(f"  Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check monitoring stats
    try:
        stats_resp = requests.get("http://localhost:8000/stats")
        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            print(f"\n  API Total Requests: {stats['total_requests']}")
            print(f"  API Fraud Rate:     {stats.get('fraud_rate', 'N/A')}")
    except:
        pass

if __name__ == "__main__":
    run_simulation(n_transactions=20, delay_seconds=1.0)
