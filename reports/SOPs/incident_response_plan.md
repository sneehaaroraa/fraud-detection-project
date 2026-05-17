# 🚨 Incident Response Plan (IRP) - Financial Fraud
## SOP-SEC-001: Automated Fraud Response

### 1. Detection (The Alert)
*   **Trigger**: ML model returns `risk_score > 0.8` (CRITICAL).
*   **Channel**: Live Dashboard + Backend Audit Log.

### 2. Triage & Analysis
*   **Step A**: Identify `transaction_id` and `customer_id`.
*   **Step B**: Check `rules_triggered`. Is it a "High-Value Transfer" + "Account Drained"?
*   **Step C**: Verify if the account has a history of similar patterns.

### 3. Containment
*   **Manual**: Admin clicks "Freeze Account" on dashboard.
*   **Automated**: Backend triggers temporary lock on withdrawal API for 1 hour.

### 4. Eradication & Recovery
*   Notify customer via SMS/Email.
*   Require Multi-Factor Authentication (MFA) to unlock.
*   Roll back the specific transaction if confirmed as unauthorized.

### 5. Post-Incident Activity
*   Update ML training set with the new fraud pattern.
*   Generate "Incident Closure Report" for compliance.
