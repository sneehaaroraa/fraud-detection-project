# 📄 Fraud Types Report
### Project: Threat Response in Digital Transactions
### Week 1 Deliverable — Domain Study

---

## 1. Introduction

Financial fraud in digital transactions is a growing threat to banks, fintech companies, and individual users. Understanding *how* fraud happens is the first step to detecting and preventing it. This report covers the four most common types of fraud found in digital payment systems.

---

## 2. Common Types of Financial Fraud

### 🔴 2.1 Account Takeover (ATO)
**What it is:** A fraudster gains unauthorized access to a legitimate user's account — typically by stealing credentials through phishing, data breaches, or brute force attacks.

**How it happens:**
- Victim receives a fake email/SMS pretending to be their bank
- Victim enters login credentials on a fake site
- Fraudster logs in, changes contact details, and drains funds

**Red flags:**
- Login from a new device/location
- Password change followed immediately by a large transfer
- Multiple failed login attempts before success

**Real-world example:** In 2021, a wave of ATO attacks targeted Indian UPI users — fraudsters called victims pretending to be bank officials and tricked them into sharing OTPs.

---

### 🔴 2.2 Internal Fraud
**What it is:** Fraud committed by employees or insiders who have privileged access to banking systems.

**How it happens:**
- Bank employee creates fake accounts and transfers funds
- Employee overrides fraud flags for specific transactions
- Collusion between insiders and external criminals

**Red flags:**
- Transactions approved outside normal business hours
- An employee account accessing records they have no business reason to view
- Repeated small transfers just below reporting thresholds ("structuring")

**Real-world example:** The infamous "salami slicing" technique — employees divert fractions of a rupee from thousands of accounts, accumulating large sums while each individual loss goes unnoticed.

---

### 🔴 2.3 Fake Transfers / Money Laundering
**What it is:** Using the financial system to move illegally obtained money so it appears legitimate.

**How it happens (3 stages):**
1. **Placement** — Dirty money enters the banking system (e.g., via cash deposits)
2. **Layering** — Multiple transfers between accounts to obscure the trail
3. **Integration** — Money re-enters the economy as "clean" funds

**Red flags in digital transactions:**
- Funds passing through many intermediate accounts rapidly
- Round-number transfers (exactly ₹1,00,000 — not ₹99,872)
- Accounts that receive large amounts and immediately send them out
- Transactions to high-risk jurisdictions

**Dataset relevance:** In PaySim, the `TRANSFER` type followed by `CASH_OUT` is a common money laundering simulation pattern.

---

### 🔴 2.4 High-Frequency Micro-Transactions
**What it is:** Many small transactions conducted in a short period — used either to test stolen cards or to gradually drain accounts below detection thresholds.

**How it happens:**
- Fraudster tests a stolen card with ₹1–₹10 purchases to check if it's active
- Once confirmed, larger fraudulent charges follow
- Or: repeated micro-transfers accumulate to a large total

**Red flags:**
- Same account making 10+ transactions within 1 hour
- Identical or near-identical amounts repeated rapidly
- High transaction velocity from the same IP/device

---

## 3. How Banks Detect Fraud — SIEM & Anomaly Detection

### SIEM (Security Information and Event Management)
SIEM tools like **Splunk** and **IBM QRadar** collect logs from all banking systems in real time and apply rules to generate alerts.

Example rule: *"Alert if a single account transfers more than ₹5 lakh within 1 hour"*

### Anomaly Detection
Machine learning models learn what "normal" behavior looks like for each user. Any deviation — unusual time, location, amount, or recipient — triggers a flag.

### Rule-Based Systems
Simpler but fast: hard-coded rules like `IF transaction_type == TRANSFER AND amount > 100000 THEN flag`.

---

## 4. Key Takeaways for This Project

| Fraud Type | Most Relevant Dataset Signal |
|---|---|
| Account Takeover | Sudden large transfer + zero new balance |
| Internal Fraud | `isFlaggedFraud` field, unusual patterns |
| Money Laundering | TRANSFER → CASH_OUT chains |
| Micro-transaction fraud | High frequency from same `nameOrig` |

---

## 5. Conclusion

Financial fraud is multi-faceted. No single rule catches all fraud — this is why this project combines **rule-based SIEM alerts** (Weeks 2–3) with **machine learning models** (Weeks 4–5) to build a layered defense system.

---
*Report prepared as part of the 6-week Threat Response in Digital Transactions project.*
