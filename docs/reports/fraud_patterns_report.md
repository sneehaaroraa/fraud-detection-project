# 📊 Fraud Pattern Analysis Report
### Project: Threat Response in Digital Transactions — Week 3

---

## 1. Executive Summary

This report presents the findings from a deep-dive analysis of fraudulent transactions in the PaySim dataset. Based on pattern analysis, **7 fraud detection rules** were developed and validated. Key findings show that fraud is highly concentrated in specific transaction types (TRANSFER and CASH_OUT) and almost always results in the complete draining of the sender's account.

---

## 2. Dataset Recap

| Metric | Value |
|---|---|
| Total Transactions | ~6.3 million |
| Fraud Cases | ~8,213 (0.13%) |
| Non-Fraud Cases | ~6.35 million (99.87%) |
| Fraudulent Transaction Types | TRANSFER and CASH_OUT **only** |

---

## 3. Key Fraud Patterns Discovered

### 3.1 Pattern 1: Fraud is Concentrated in Two Transaction Types

Fraud **only** occurs in `TRANSFER` and `CASH_OUT` transactions:

| Transaction Type | Fraud Rate |
|---|---|
| TRANSFER | ~0.77% |
| CASH_OUT | ~0.18% |
| PAYMENT | 0.00% |
| DEBIT | 0.00% |
| CASH_IN | 0.00% |

**Implication:** Rules that check `type == TRANSFER OR CASH_OUT` can immediately filter out 65% of all transactions from fraud analysis, reducing false positive alerts significantly.

---

### 3.2 Pattern 2: Accounts Are Completely Drained

In **over 99%** of confirmed fraud cases, the sender's balance after the transaction (`new_balance_sender`) drops to exactly **₹0**.

This is the **single strongest rule-based signal** in the dataset.

**Reason:** Fraudsters want to extract maximum value from a compromised account in a single operation before the victim notices.

**Rule created:** `RULE_003 — Account Completely Drained`

---

### 3.3 Pattern 3: High-Value Amounts

Fraudulent transactions tend to involve **significantly higher amounts** than legitimate ones:

| Metric | Fraud | Legitimate |
|---|---|---|
| Mean Amount | ~₹1,467,412 | ~₹179,862 |
| Median Amount | ~₹744,956 | ~₹74,871 |

This 8× difference in mean amount makes `amount` one of the strongest features for ML models in Week 5.

**Rules created:** `RULE_001` (TRANSFER > ₹100K), `RULE_002` (CASH_OUT > ₹200K), `RULE_005` (any > ₹500K)

---

### 3.4 Pattern 4: The Bank's Own Flag Misses 99.8% of Fraud

The `isFlaggedFraud` column represents the bank's existing rule engine. It caught only **16 out of 8,213 fraud cases** (0.2%).

This demonstrates exactly why this project exists — current systems are inadequate. ML + better rules are needed.

---

### 3.5 Pattern 5: High-Frequency Activity

Some accounts send 3–5 transactions within the same 1-hour step. When correlated with fraud, these accounts show elevated risk. High-frequency patterns are used by fraudsters for:
- Testing stolen card credentials with small amounts
- Rapidly distributing laundered funds across multiple accounts

---

### 3.6 Pattern 6: Zero-Balance Origin Accounts

Some fraudulent transactions originate from accounts with **₹0 pre-transaction balance**. These are likely ghost accounts created specifically for fraud.

---

## 4. Fraud Detection Rules Summary

| Rule ID | Name | Condition | Severity | Fraud Coverage |
|---|---|---|---|---|
| RULE_001 | High-Value TRANSFER | type=TRANSFER AND amount>100K | HIGH | ~60% |
| RULE_002 | High-Value CASH_OUT | type=CASH_OUT AND amount>200K | HIGH | ~35% |
| RULE_003 | Account Drained | new_balance_sender=0 AND amount>50K | HIGH | ~99% |
| RULE_004 | Bank Internal Flag | isFlaggedFraud=1 | HIGH | 0.2% |
| RULE_005 | Very Large Amount | amount>500K | MEDIUM | ~45% |
| RULE_006 | High-Frequency Account | 3+ tx from same account in 1 hour | MEDIUM | Variable |
| RULE_007 | Zero Origin Balance | old_balance_sender=0 AND amount>0 | MEDIUM | ~20% |

> **Note:** Rules overlap — a single fraud transaction may trigger multiple rules. `RULE_003` has the highest individual coverage (~99%) and is recommended as the **primary rule**.

---

## 5. Recommendations for SIEM Implementation

1. **Deploy RULE_003 as the primary alert** — highest recall, lowest false negatives
2. **Use RULE_001 and RULE_002 as secondary alerts** — catches additional cases RULE_003 misses
3. **Use RULE_005, RULE_006, RULE_007 for investigation queues** — medium priority, review manually
4. **Do NOT rely on RULE_004 alone** — bank's internal flag has extremely low recall
5. **Combine rule alerts with ML scores** (Week 5) for maximum precision

---

## 6. Files Produced This Week

| File | Description |
|---|---|
| `week3_fraud_rules.py` | Full analysis and rule application code |
| `fraud_detection_rules.yaml` | 7 rules in SIEM-compatible YAML format |
| `fraud_detection_rules.json` | Same rules in JSON format |
| `fraud_insight_visuals.png` | 6-panel dashboard of fraud patterns |
| `fraud_patterns_report.md` | This report |

---
*Week 3 complete. Proceeding to Weeks 4–5: ML Model Development (Random Forest, XGBoost, SHAP).*
