# =============================================================
# WEEK 2: DATA CLEANING & LOG PREPARATION FOR SIEM INTEGRATION
# =============================================================
# 📌 What this file does:
#   - Loads the cleaned dataset from Week 1 (or raw dataset)
#   - Further cleans and validates data types
#   - Converts each row into a JSON log (like a real SIEM log)
#   - Simulates timestamps from the 'step' field
#   - Exports test samples (fraud + non-fraud) for rule testing
#
# ▶️ How to run:
#   python week2_log_preparation.py
# =============================================================

import pandas as pd
import json
import os
from datetime import datetime, timedelta

# Create output folders
os.makedirs("data", exist_ok=True)
os.makedirs("reports", exist_ok=True)
os.makedirs("logs", exist_ok=True)

print("="*60)
print("🚀 WEEK 2: DATA CLEANING & SIEM LOG PREPARATION")
print("="*60)

# ── STEP 1: Load Dataset ──────────────────────────────────────
# Try loading cleaned version from Week 1; fall back to raw CSV

try:
    df = pd.read_csv("data/cleaned_dataset.csv")
    print(f"✅ Loaded cleaned dataset: {df.shape[0]:,} rows")
except FileNotFoundError:
    print("⚠️  Cleaned dataset not found. Loading raw dataset...")
    df = pd.read_csv("PS_20174392719_1491204439457_log.csv")  # ← UPDATE PATH IF NEEDED
    print(f"✅ Loaded raw dataset: {df.shape[0]:,} rows")

# ── STEP 2: Data Cleaning ─────────────────────────────────────
print("\n" + "="*60)
print("🧹 STEP 2: DATA CLEANING")
print("="*60)

# 2a. Check and remove duplicates
duplicates = df.duplicated().sum()
print(f"  Duplicate rows found: {duplicates}")
df = df.drop_duplicates()

# 2b. Check for null/missing values
nulls = df.isnull().sum()
print(f"  Missing values:\n{nulls[nulls > 0] if nulls.sum() > 0 else '  ✅ None found'}")
df = df.dropna()  # Drop any rows with nulls

# 2c. Ensure correct data types
# 'step' should be integer, 'amount' should be float, 'isFraud' should be int
df['step'] = df['step'].astype(int)
df['amount'] = df['amount'].astype(float)
df['isFraud'] = df['isFraud'].astype(int)
df['isFlaggedFraud'] = df['isFlaggedFraud'].astype(int)

# 2d. Remove nonsensical rows where amount is 0 or negative
invalid_amount = df[df['amount'] <= 0].shape[0]
print(f"  Rows with amount ≤ 0 (removed): {invalid_amount}")
df = df[df['amount'] > 0]

print(f"\n  ✅ Cleaned dataset shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ── STEP 3: Rename Columns to Log-Friendly Names ─────────────
# SIEM tools prefer lowercase, underscore-separated names
# This makes logs readable by Splunk/ELK

print("\n" + "="*60)
print("🔄 STEP 3: RENAMING COLUMNS TO LOG-FRIENDLY FORMAT")
print("="*60)

rename_map = {
    'nameOrig': 'account_from',
    'nameDest': 'account_to',
    'oldbalanceOrg': 'old_balance_sender',
    'newbalanceOrig': 'new_balance_sender',
    'oldbalanceDest': 'old_balance_receiver',
    'newbalanceDest': 'new_balance_receiver',
}

# Only rename columns that exist (handles both raw and cleaned versions)
rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
df = df.rename(columns=rename_map)

print("  Column mapping applied:")
for old, new in rename_map.items():
    print(f"    {old:25s} → {new}")

# ── STEP 4: Simulate Timestamps ───────────────────────────────
# The 'step' column is just a number (1 to 744 = 30 days of hours)
# We convert it to a real datetime starting from Jan 1, 2023

print("\n" + "="*60)
print("⏰ STEP 4: SIMULATING TIMESTAMPS")
print("="*60)

BASE_DATE = datetime(2023, 1, 1, 0, 0, 0)

# Each 'step' unit = 1 hour
df['timestamp'] = df['step'].apply(
    lambda s: (BASE_DATE + timedelta(hours=int(s))).strftime('%Y-%m-%dT%H:%M:%SZ')
)

print(f"  ✅ Timestamp range: {df['timestamp'].min()} → {df['timestamp'].max()}")
print(f"  Example: step=1 → {df[df['step']==1]['timestamp'].values[0]}")

# ── STEP 5: Add SIEM Enrichment Fields ────────────────────────
# Real SIEM logs have extra metadata fields like severity, host, source
# We simulate these based on fraud rules

print("\n" + "="*60)
print("🏷️  STEP 5: ADDING SIEM ENRICHMENT FIELDS")
print("="*60)

def assign_severity(row):
    """
    Assigns a severity level to a transaction based on risk signals.
    This is a simplified version of what a SIEM rule engine does.
    """
    if row['isFraud'] == 1:
        return 'CRITICAL'
    elif row['type'] == 'TRANSFER' and row['amount'] > 100_000:
        return 'HIGH'
    elif row['new_balance_sender'] == 0 and row['amount'] > 50_000:
        return 'HIGH'
    elif row['amount'] > 200_000:
        return 'MEDIUM'
    else:
        return 'LOW'

df['severity'] = df.apply(assign_severity, axis=1)
df['host'] = 'fintech-core-server'          # Simulated source system
df['source'] = 'mobile_payment_platform'    # Simulated data source
df['event_type'] = 'financial_transaction'  # SIEM event category

print("  ✅ Added fields: severity, host, source, event_type")
print(f"\n  Severity distribution:\n{df['severity'].value_counts()}")

# ── STEP 6: Save Cleaned Dataset CSV ─────────────────────────
df.to_csv('data/cleaned_dataset.csv', index=False)
print(f"\n  ✅ Cleaned dataset saved → data/cleaned_dataset.csv")

# ── STEP 7: Convert to JSON Logs ──────────────────────────────
# SIEM tools like Splunk/ELK ingest data as JSON events
# Each transaction becomes one JSON log entry

print("\n" + "="*60)
print("📄 STEP 6: CONVERTING TO JSON LOG FORMAT")
print("="*60)

# For large datasets, save first 50,000 rows as JSON (full file would be huge)
# In a real project you'd stream this or chunk it
sample_size = min(50_000, len(df))
df_log_sample = df.sample(sample_size, random_state=42)

log_records = df_log_sample.to_dict(orient='records')

with open('logs/transaction_logs.json', 'w') as f:
    json.dump(log_records, f, indent=2)

print(f"  ✅ JSON logs saved → logs/transaction_logs.json")
print(f"     ({sample_size:,} transaction records)")

# Show what one log looks like
print("\n  📋 Example JSON log entry:")
example = log_records[0]
print(json.dumps(example, indent=4))

# Also save as CSV for easy viewing
df_log_sample.to_csv('logs/transaction_logs.csv', index=False)
print(f"\n  ✅ CSV logs also saved → logs/transaction_logs.csv")

# ── STEP 8: Create Test Samples for Rule Testing ─────────────
# For Week 3, we need a small set of known fraud + non-fraud cases
# to test our alert rules against

print("\n" + "="*60)
print("🧪 STEP 7: CREATING FRAUD TEST SAMPLE")
print("="*60)

# Get 8 confirmed fraud cases
fraud_samples = df[df['isFraud'] == 1].sample(8, random_state=42)

# Get 7 confirmed non-fraud cases (mix of types)
non_fraud_samples = df[df['isFraud'] == 0].sample(7, random_state=42)

# Combine
test_sample = pd.concat([fraud_samples, non_fraud_samples]).sample(frac=1, random_state=42)
test_sample = test_sample.reset_index(drop=True)

# Save as CSV
test_sample.to_csv('data/test_logs_sample.csv', index=False)

# Save as JSON
test_records = test_sample.to_dict(orient='records')
with open('data/fraud_cases_sample.json', 'w') as f:
    json.dump(test_records, f, indent=2)

print(f"  ✅ Test sample saved → data/test_logs_sample.csv")
print(f"  ✅ Test sample saved → data/fraud_cases_sample.json")
print(f"     Fraud cases: {fraud_samples.shape[0]}")
print(f"     Non-fraud cases: {non_fraud_samples.shape[0]}")

# ── STEP 9: Summary ───────────────────────────────────────────
print("\n" + "="*60)
print("🎉 WEEK 2 COMPLETE!")
print("="*60)
print("""
Files created:
  📁 data/
      ├── cleaned_dataset.csv         ← Full cleaned dataset
      ├── test_logs_sample.csv        ← 15 test events (fraud + not)
      └── fraud_cases_sample.json     ← Same, in JSON

  📁 logs/
      ├── transaction_logs.json       ← SIEM-ready JSON logs
      └── transaction_logs.csv        ← Same, in CSV format

  📁 reports/
      └── week2_data_prep_notes.md    ← (run the notes script)
""")
