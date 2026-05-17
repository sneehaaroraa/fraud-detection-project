# FraudEye Pro: SIEM Integration Guide

### 📂 Splunk Alerts (splunk_alerts.conf)
```ini
[FraudDetection_HighRisk]
search = sourcetype="fraudeye_json" risk_level="CRITICAL" OR risk_level="HIGH"
alert.severity = 4
alert.suppress = 1
alert.suppress.fields = transaction_id
action.email = 1
action.email.to = soc-alerts@company.com
```

### 📊 Kibana Filter (JSON)
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "prediction": "FRAUD" } },
        { "range": { "amount": { "gte": 100000 } } }
      ]
    }
  }
}
```

### 🔍 Insider Threat Logic (SQL Query)
```sql
-- Identify accounts with 5+ high-value transfers in < 1 hour
SELECT account_id, COUNT(*) as txn_count
FROM transaction_audit
WHERE timestamp > datetime('now', '-1 hour')
  AND amount > 50000
GROUP BY account_id
HAVING txn_count >= 5;
```
