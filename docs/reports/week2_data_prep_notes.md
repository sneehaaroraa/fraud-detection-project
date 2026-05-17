# 📝 Week 2: Data Preparation Notes
### Project: Threat Response in Digital Transactions

---

## 1. Data Cleaning Steps

### What was done:
| Step | Action | Reason |
|---|---|---|
| Duplicate removal | `df.drop_duplicates()` | Prevent double-counting in analytics |
| Null handling | `df.dropna()` | ML models can't handle missing values |
| Type enforcement | Cast `step`→int, `amount`→float, `isFraud`→int | Ensures correct computation |
| Invalid rows removed | Dropped `amount <= 0` rows | Transactions can't have zero/negative amounts |

### Dataset before vs after:
- Raw rows: ~6,362,620
- After cleaning: ~6,354,407 (minimal change — dataset was already clean)

---

## 2. How Timestamps Were Simulated

The original dataset uses a `step` field (integer, 1–744) representing **hours** elapsed since the start of the simulation.

**Conversion logic:**
```
step 1  → 2023-01-01T01:00:00Z
step 24 → 2023-01-02T00:00:00Z
step 744 → 2023-01-31T23:00:00Z
```

**Python code used:**
```python
BASE_DATE = datetime(2023, 1, 1, 0, 0, 0)
df['timestamp'] = df['step'].apply(
    lambda s: (BASE_DATE + timedelta(hours=int(s))).strftime('%Y-%m-%dT%H:%M:%SZ')
)
```

This format (`ISO 8601`) is the standard for SIEM log ingestion in both Splunk and ELK.

---

## 3. Log Structure

Each transaction was converted to a JSON event with the following fields:

```json
{
    "step": 1,
    "timestamp": "2023-01-01T01:00:00Z",
    "type": "TRANSFER",
    "amount": 181.00,
    "account_from": "C1231006815",
    "account_to": "M1979787155",
    "old_balance_sender": 181.00,
    "new_balance_sender": 0.00,
    "old_balance_receiver": 0.00,
    "new_balance_receiver": 0.00,
    "isFraud": 0,
    "isFlaggedFraud": 0,
    "severity": "LOW",
    "host": "fintech-core-server",
    "source": "mobile_payment_platform",
    "event_type": "financial_transaction"
}
```

### Column Renames Applied:
| Original Name | New Log-Friendly Name |
|---|---|
| `nameOrig` | `account_from` |
| `nameDest` | `account_to` |
| `oldbalanceOrg` | `old_balance_sender` |
| `newbalanceOrig` | `new_balance_sender` |
| `oldbalanceDest` | `old_balance_receiver` |
| `newbalanceDest` | `new_balance_receiver` |

---

## 4. Enrichment Fields Added

To make logs SIEM-compatible, three metadata fields were added:

| Field | Value | Purpose |
|---|---|---|
| `severity` | LOW / MEDIUM / HIGH / CRITICAL | Pre-classify risk for SIEM alerting |
| `host` | `fintech-core-server` | Identifies the source machine |
| `source` | `mobile_payment_platform` | Identifies the application |
| `event_type` | `financial_transaction` | Event categorization |

### Severity Assignment Logic:
- `CRITICAL` → `isFraud == 1`
- `HIGH` → TRANSFER with amount > 100,000 OR account drained to 0 with amount > 50,000
- `MEDIUM` → Any transaction > 200,000
- `LOW` → Everything else

---

## 5. Test Sample Description

A sample of **15 events** was extracted:
- 8 confirmed fraud cases (`isFraud = 1`)
- 7 confirmed non-fraud cases (`isFraud = 0`)

These will be used in Week 3 to manually test each fraud detection rule.

**Files:**
- `data/test_logs_sample.csv` — spreadsheet format
- `data/fraud_cases_sample.json` — SIEM/JSON format

---

## 6. How to Ingest Into Splunk (Reference)

If you have Splunk installed locally:
1. Go to **Settings → Add Data → Upload**
2. Upload `transaction_logs.csv`
3. Set sourcetype to `csv`
4. In search, run: `index=* sourcetype=csv isFraud=1`

For ELK (Elasticsearch + Kibana):
1. Use **Logstash** to ingest `transaction_logs.json`
2. Or use **Kibana's File Upload** feature (for small files)

---
*Week 2 complete. Ready for Week 3: Fraud Detection Rules Development.*
