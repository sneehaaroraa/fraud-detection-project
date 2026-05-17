# 📝 Week 1 Summary Report
### Project: Threat Response in Digital Transactions

---

## 1. Domain Learnings

This week I studied four major types of financial fraud:
- **Account Takeover** — credentials stolen, account drained
- **Internal Fraud** — insider manipulation of banking systems
- **Money Laundering** — layered transfers to hide illegal money (most relevant to our dataset)
- **Micro-transaction Fraud** — high-frequency small transfers to evade detection

Banks use SIEM tools (Splunk, ELK) and ML anomaly detection together to catch fraud. No single method is sufficient alone.

---

## 2. Dataset Overview

**Dataset:** PaySim — Simulated Mobile Money Transactions  
**Source:** Kaggle (based on real transaction logs from a mobile money service in Africa)

| Property | Value |
|---|---|
| Total Rows | ~6.3 million transactions |
| Columns | 11 |
| Fraud Cases | ~8,213 (≈ 0.13% of all transactions) |
| Time Period | 744 steps (≈ 30 days of hourly data) |

**Key Columns:**
- `step` → Hour number (1–744)
- `type` → CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER
- `amount` → Transaction value
- `nameOrig / nameDest` → Sender / receiver account IDs
- `isFraud` → Ground truth label (1 = fraud)

---

## 3. Key Insights from EDA

### 3.1 Transaction Types
- **CASH_OUT** is the most common transaction type (~35%)
- **PAYMENT** is second most common (~34%)
- **TRANSFER** and **CASH_OUT** are the **only** types that contain fraud

### 3.2 Fraud Patterns Discovered
1. **Fraud is extremely rare** — only ~0.13% of transactions, making this a highly imbalanced dataset. This means ML models must be evaluated with Precision/Recall, not accuracy.
2. **Fraud drains accounts** — In ~99% of fraud cases, the sender's new balance becomes exactly ₹0. This is a very strong fraud signal.
3. **High-value transactions dominate fraud** — Most fraudulent TRANSFER transactions involve amounts above ₹100,000.
4. **Fraud peaks mid-month** — Fraud activity (by step count) is not uniform; it clusters in certain time windows.
5. **Destination accounts are targeted repeatedly** — A small set of `nameDest` accounts receive multiple fraudulent transfers.

### 3.3 Anomalies Spotted
- Several transactions show `oldbalanceOrg = 0` AND `amount > 0` — meaning the sender had no money but a transaction was recorded. This suggests synthetic or fraudulent log injection.
- `isFlaggedFraud` catches only 16 out of 8,213 fraud cases — the bank's own rule system is very inadequate.

---

## 4. Areas to Focus on in Week 2

1. **Convert `step` to real timestamps** — for SIEM log ingestion
2. **Rename columns** to log-friendly names (e.g., `nameOrig` → `account_from`)
3. **Separate fraud/non-fraud test samples** — to test Week 3 alert rules
4. **Format data as JSON** — for Splunk/ELK ingestion simulation

---

## 5. Files Produced This Week

| File | Description |
|---|---|
| `fraud_types_report.md` | 2-page domain research writeup |
| `week1_data_exploration.py` | Full EDA script with comments |
| `data/cleaned_dataset.csv` | Cleaned dataset with timestamps added |
| `outputs/plots/*.png` | 5 EDA visualizations |

---
*Week 1 complete. Moving to Week 2: Data Cleaning & SIEM Log Preparation.*
