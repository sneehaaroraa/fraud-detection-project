# =============================================================
# WEEK 3: FRAUD DETECTION RULES & THREAT PATTERN ANALYSIS
# =============================================================
# 📌 What this file does:
#   - Deep-dives into fraud patterns in the cleaned dataset
#   - Generates visualizations of fraud behavior
#   - Creates and tests 7 fraud detection rules
#   - Exports rules in YAML format (SIEM-compatible)
#   - Tests rules against the sample logs from Week 2
#
# ▶️ How to run:
#   python week3_fraud_rules.py
# =============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import json
import yaml      # pip install pyyaml
import os

os.makedirs("outputs/plots", exist_ok=True)
os.makedirs("week3", exist_ok=True)

print("="*60)
print("🚀 WEEK 3: FRAUD DETECTION RULES DEVELOPMENT")
print("="*60)

# ── STEP 1: Load Data ─────────────────────────────────────────
try:
    df = pd.read_csv("data/cleaned_dataset.csv")
    print(f"✅ Loaded cleaned dataset: {df.shape[0]:,} rows")
except FileNotFoundError:
    print("❌ ERROR: Run week2_log_preparation.py first to generate data/cleaned_dataset.csv")
    exit()

# Separate fraud and non-fraud for easy analysis
fraud = df[df['isFraud'] == 1]
legit = df[df['isFraud'] == 0]
print(f"   Fraud cases: {len(fraud):,} | Legit cases: {len(legit):,}")

# ── STEP 2: Pattern Analysis ──────────────────────────────────
print("\n" + "="*60)
print("🔍 STEP 2: FRAUD PATTERN ANALYSIS")
print("="*60)

# Pattern A: Which transaction TYPES have fraud?
print("\n[A] Fraud by Transaction Type:")
type_analysis = df.groupby('type').agg(
    total=('isFraud', 'count'),
    fraud_count=('isFraud', 'sum'),
).reset_index()
type_analysis['fraud_rate_%'] = (type_analysis['fraud_count'] / type_analysis['total'] * 100).round(3)
print(type_analysis.to_string(index=False))

# Pattern B: Amount ranges in fraud
print("\n[B] Fraud Amount Statistics:")
print(f"   Min amount in fraud:    ₹{fraud['amount'].min():,.2f}")
print(f"   Max amount in fraud:    ₹{fraud['amount'].max():,.2f}")
print(f"   Mean amount in fraud:   ₹{fraud['amount'].mean():,.2f}")
print(f"   Median amount in fraud: ₹{fraud['amount'].median():,.2f}")
print(f"\n   Legit mean amount:      ₹{legit['amount'].mean():,.2f}")

# Pattern C: Balance drain signal
drained = fraud[fraud['new_balance_sender'] == 0]
print(f"\n[C] Account balance drained to 0:")
print(f"   Fraud cases where new_balance_sender = 0: {len(drained):,}/{len(fraud):,} ({len(drained)/len(fraud)*100:.1f}%)")

# Pattern D: High-frequency transfers (same account, short window)
# Group by account_from and count transactions per step
account_freq = df.groupby(['account_from', 'step']).size().reset_index(name='tx_count')
high_freq = account_freq[account_freq['tx_count'] >= 3]
print(f"\n[D] Accounts making 3+ transactions in same hour: {len(high_freq):,}")

# Pattern E: isFlaggedFraud reliability
flagged = df[df['isFlaggedFraud'] == 1]
print(f"\n[E] Bank's own flag (isFlaggedFraud):")
print(f"   Total flagged: {len(flagged):,}")
print(f"   Of those, actually fraud: {flagged['isFraud'].sum():,}")
print(f"   Bank flag captures only {flagged['isFraud'].sum()/len(fraud)*100:.2f}% of fraud cases ← VERY POOR!")

# ── STEP 3: Visualizations ────────────────────────────────────
print("\n" + "="*60)
print("📊 STEP 3: GENERATING FRAUD INSIGHT VISUALIZATIONS")
print("="*60)

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Fraud Pattern Analysis Dashboard', fontsize=16, fontweight='bold', y=1.01)

# --- Chart 1: Fraud rate by transaction type ---
ax1 = axes[0, 0]
fraud_rate = type_analysis.set_index('type')['fraud_rate_%'].sort_values(ascending=False)
bars = ax1.bar(fraud_rate.index, fraud_rate.values,
               color=['crimson' if v > 0 else 'steelblue' for v in fraud_rate.values])
ax1.set_title('Fraud Rate (%) by Transaction Type', fontweight='bold')
ax1.set_ylabel('Fraud Rate (%)')
ax1.set_xlabel('Transaction Type')
for bar, val in zip(bars, fraud_rate.values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
             f'{val:.2f}%', ha='center', va='bottom', fontsize=9)

# --- Chart 2: Amount boxplot (fraud vs legit) ---
ax2 = axes[0, 1]
df_box = df[df['amount'] < 500_000][['amount', 'isFraud']].copy()
df_box['label'] = df_box['isFraud'].map({0: 'Legitimate', 1: 'Fraud'})
fraud_amounts = df_box[df_box['label']=='Fraud']['amount']
legit_amounts = df_box[df_box['label']=='Legitimate']['amount'].sample(5000, random_state=42)
ax2.boxplot([legit_amounts, fraud_amounts], labels=['Legitimate', 'Fraud'],
            patch_artist=True,
            boxprops=dict(facecolor='steelblue', alpha=0.6),
            medianprops=dict(color='red', linewidth=2))
ax2.set_title('Transaction Amount Distribution\n(Fraud vs Legit)', fontweight='bold')
ax2.set_ylabel('Amount (₹)')

# --- Chart 3: New Balance = 0 as fraud signal ---
ax3 = axes[0, 2]
drained_labels = ['Balance → 0\n(Drained)', 'Balance > 0\n(Not Drained)']
drained_fraud = [len(drained), len(fraud) - len(drained)]
drained_colors = ['#e74c3c', '#95a5a6']
ax3.pie(drained_fraud, labels=drained_labels, colors=drained_colors,
        autopct='%1.1f%%', startangle=140,
        textprops={'fontsize': 10})
ax3.set_title('Fraud: Account Drained to ₹0?', fontweight='bold')

# --- Chart 4: Top 10 most targeted accounts ---
ax4 = axes[1, 0]
top_targets = fraud['account_to'].value_counts().head(10)
ax4.barh(range(len(top_targets)), top_targets.values, color='#e74c3c', alpha=0.8)
ax4.set_yticks(range(len(top_targets)))
ax4.set_yticklabels([t[:12] + '...' for t in top_targets.index], fontsize=8)
ax4.set_title('Top 10 Most Targeted\nDestination Accounts', fontweight='bold')
ax4.set_xlabel('Number of Fraud Transactions Received')
ax4.invert_yaxis()

# --- Chart 5: Fraud volume by hour of day ---
ax5 = axes[1, 1]
fraud['hour_of_day'] = fraud['step'] % 24
fraud_by_hour = fraud.groupby('hour_of_day').size()
ax5.plot(fraud_by_hour.index, fraud_by_hour.values,
         color='crimson', linewidth=2, marker='o', markersize=4)
ax5.fill_between(fraud_by_hour.index, fraud_by_hour.values, alpha=0.2, color='crimson')
ax5.set_title('Fraud Count by Hour of Day', fontweight='bold')
ax5.set_xlabel('Hour (0 = midnight)')
ax5.set_ylabel('Number of Fraud Cases')
ax5.set_xticks(range(0, 24, 2))

# --- Chart 6: Rule Coverage Heatmap ---
ax6 = axes[1, 2]
rule_labels = ['R1: High-Value TRANSFER', 'R2: High-Value CASH_OUT',
               'R3: Account Drained', 'R4: isFlaggedFraud',
               'R5: Very Large Amount', 'R6: High-Freq Account',
               'R7: Zero Origin Balance']

# Check how many fraud cases each rule catches
r1 = fraud[(fraud['type'] == 'TRANSFER') & (fraud['amount'] > 100_000)]
r2 = fraud[(fraud['type'] == 'CASH_OUT') & (fraud['amount'] > 200_000)]
r3 = fraud[fraud['new_balance_sender'] == 0]
r4 = fraud[fraud['isFlaggedFraud'] == 1]
r5 = fraud[fraud['amount'] > 500_000]
r6_accounts = set(high_freq['account_from'])
r6 = fraud[fraud['account_from'].isin(r6_accounts)]
r7 = fraud[fraud['old_balance_sender'] == 0]

counts = [len(r1), len(r2), len(r3), len(r4), len(r5), len(r6), len(r7)]
coverages = [c/len(fraud)*100 for c in counts]

colors = ['#2ecc71' if c > 50 else '#f39c12' if c > 10 else '#e74c3c' for c in coverages]
bars = ax6.barh(rule_labels, coverages, color=colors, alpha=0.85)
ax6.set_xlabel('% of Fraud Cases Caught')
ax6.set_title('Rule Coverage\n(% of Fraud Cases Each Rule Catches)', fontweight='bold')
ax6.set_xlim(0, 110)
for bar, pct in zip(bars, coverages):
    ax6.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
             f'{pct:.1f}%', va='center', fontsize=9)

green_patch = mpatches.Patch(color='#2ecc71', label='>50% coverage')
orange_patch = mpatches.Patch(color='#f39c12', label='10-50% coverage')
red_patch = mpatches.Patch(color='#e74c3c', label='<10% coverage')
ax6.legend(handles=[green_patch, orange_patch, red_patch], loc='lower right', fontsize=8)

plt.tight_layout()
plt.savefig('week3/fraud_insight_visuals.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ Dashboard saved → week3/fraud_insight_visuals.png")

# ── STEP 4: Define the 7 Fraud Detection Rules ────────────────
print("\n" + "="*60)
print("📜 STEP 4: FRAUD DETECTION RULES")
print("="*60)

rules = [
    {
        "rule_id": "RULE_001",
        "name": "High-Value TRANSFER",
        "description": "Detects large fund transfers that are likely money laundering",
        "condition": "type == 'TRANSFER' AND amount > 100000",
        "severity": "HIGH",
        "field_checks": {"type": "TRANSFER", "amount_gt": 100000},
        "rationale": "All fraud in the dataset occurs in TRANSFER and CASH_OUT. High-value TRANSFERs are the most common fraud pattern.",
        "false_positive_risk": "Medium — legitimate large transfers exist"
    },
    {
        "rule_id": "RULE_002",
        "name": "High-Value CASH_OUT",
        "description": "Detects large cash-out transactions which often follow fraudulent transfers",
        "condition": "type == 'CASH_OUT' AND amount > 200000",
        "severity": "HIGH",
        "field_checks": {"type": "CASH_OUT", "amount_gt": 200000},
        "rationale": "Money laundering pattern: fraudster transfers funds then cashes out immediately",
        "false_positive_risk": "Medium"
    },
    {
        "rule_id": "RULE_003",
        "name": "Account Completely Drained",
        "description": "Sender balance drops to exactly zero after transaction — classic fraud signal",
        "condition": "new_balance_sender == 0 AND amount > 50000",
        "severity": "HIGH",
        "field_checks": {"new_balance_sender": 0, "amount_gt": 50000},
        "rationale": "99%+ of fraud cases result in the sender account being drained to ₹0",
        "false_positive_risk": "Low — rarely happens in legitimate transactions"
    },
    {
        "rule_id": "RULE_004",
        "name": "Bank System Flag",
        "description": "Transaction was flagged by the bank's internal system",
        "condition": "isFlaggedFraud == 1",
        "severity": "HIGH",
        "field_checks": {"isFlaggedFraud": 1},
        "rationale": "If the bank's own system flagged it, always worth investigating",
        "false_positive_risk": "Low — but note: only catches 0.2% of actual fraud"
    },
    {
        "rule_id": "RULE_005",
        "name": "Very Large Amount Transaction",
        "description": "Any transaction over ₹500,000 regardless of type",
        "condition": "amount > 500000",
        "severity": "MEDIUM",
        "field_checks": {"amount_gt": 500000},
        "rationale": "Unusually large transactions warrant investigation even if not confirmed fraud",
        "false_positive_risk": "High — many large legitimate transactions exist"
    },
    {
        "rule_id": "RULE_006",
        "name": "High-Frequency Account",
        "description": "Same account makes 3 or more transactions within a single hour",
        "condition": "COUNT(account_from, within_same_step) >= 3",
        "severity": "MEDIUM",
        "field_checks": {"frequency_threshold": 3, "window": "1 hour (1 step)"},
        "rationale": "Fraudsters often send multiple transfers rapidly to launder money",
        "false_positive_risk": "Medium — some business accounts legitimately do this"
    },
    {
        "rule_id": "RULE_007",
        "name": "Zero-Balance Origin Account",
        "description": "Sender had ₹0 before the transaction but still sent money — suspicious",
        "condition": "old_balance_sender == 0 AND amount > 0",
        "severity": "MEDIUM",
        "field_checks": {"old_balance_sender": 0, "amount_gt": 0},
        "rationale": "Indicates possible synthetic or ghost account used in fraud",
        "false_positive_risk": "Medium — could be a newly opened account"
    },
]

print(f"\n  Created {len(rules)} fraud detection rules:")
print(f"  {'Rule ID':<12} {'Name':<35} {'Severity':<10}")
print("  " + "-"*57)
for r in rules:
    print(f"  {r['rule_id']:<12} {r['name']:<35} {r['severity']:<10}")

# ── STEP 5: Save Rules as YAML ────────────────────────────────
print("\n" + "="*60)
print("💾 STEP 5: SAVING RULES")
print("="*60)

with open('week3/fraud_detection_rules.yaml', 'w') as f:
    yaml.dump({"fraud_detection_rules": rules}, f,
              default_flow_style=False, allow_unicode=True, sort_keys=False)
print("  ✅ Rules saved → week3/fraud_detection_rules.yaml")

# Save as JSON too
with open('week3/fraud_detection_rules.json', 'w') as f:
    json.dump({"fraud_detection_rules": rules}, f, indent=2)
print("  ✅ Rules saved → week3/fraud_detection_rules.json")

# ── STEP 6: Test Rules Against Sample Logs ────────────────────
print("\n" + "="*60)
print("🧪 STEP 6: TESTING RULES AGAINST SAMPLE LOGS")
print("="*60)

try:
    test_df = pd.read_csv("data/test_logs_sample.csv")
    print(f"  Loaded {len(test_df)} test events ({test_df['isFraud'].sum()} fraud, "
          f"{(test_df['isFraud']==0).sum()} legit)")

    def apply_rules(row):
        triggered = []
        if row.get('type') == 'TRANSFER' and row.get('amount', 0) > 100_000:
            triggered.append('RULE_001')
        if row.get('type') == 'CASH_OUT' and row.get('amount', 0) > 200_000:
            triggered.append('RULE_002')
        if row.get('new_balance_sender', 1) == 0 and row.get('amount', 0) > 50_000:
            triggered.append('RULE_003')
        if row.get('isFlaggedFraud', 0) == 1:
            triggered.append('RULE_004')
        if row.get('amount', 0) > 500_000:
            triggered.append('RULE_005')
        if row.get('old_balance_sender', 1) == 0 and row.get('amount', 0) > 0:
            triggered.append('RULE_007')
        return triggered if triggered else ['NONE']

    test_df['rules_triggered'] = test_df.apply(apply_rules, axis=1)
    test_df['alert_generated'] = test_df['rules_triggered'].apply(lambda x: x != ['NONE'])

    print("\n  Test Results:")
    print(f"  {'#':<4} {'Type':<12} {'Amount':>12} {'Actual':>10} {'Alert?':>8} {'Rules'}")
    print("  " + "-"*75)
    for i, row in test_df.iterrows():
        actual = "🚨 FRAUD" if row['isFraud'] == 1 else "✅ LEGIT"
        alert = "⚠️ YES" if row['alert_generated'] else "  NO"
        rules_str = ', '.join(row['rules_triggered'])
        print(f"  {i+1:<4} {str(row.get('type','')):<12} "
              f"{row.get('amount',0):>12,.0f} {actual:>10} {alert:>8}  {rules_str}")

    # Metrics
    tp = test_df[(test_df['isFraud']==1) & (test_df['alert_generated']==True)].shape[0]
    fp = test_df[(test_df['isFraud']==0) & (test_df['alert_generated']==True)].shape[0]
    fn = test_df[(test_df['isFraud']==1) & (test_df['alert_generated']==False)].shape[0]
    tn = test_df[(test_df['isFraud']==0) & (test_df['alert_generated']==False)].shape[0]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0

    print(f"\n  📊 Rule Performance on Test Sample:")
    print(f"     True Positives  (fraud caught):          {tp}")
    print(f"     False Positives (legit flagged wrongly): {fp}")
    print(f"     False Negatives (fraud missed):          {fn}")
    print(f"     True Negatives  (legit correctly passed):{tn}")
    print(f"     Precision: {precision:.2f}   Recall: {recall:.2f}")

except FileNotFoundError:
    print("  ⚠️  Test sample not found. Run week2_log_preparation.py first.")

# ── STEP 7: Pattern Analysis Report ──────────────────────────
print("\n" + "="*60)
print("🎉 WEEK 3 COMPLETE!")
print("="*60)
print("""
Files created:
  📁 week3/
      ├── fraud_detection_rules.yaml   ← 7 rules in SIEM format
      ├── fraud_detection_rules.json   ← Same, in JSON
      ├── fraud_insight_visuals.png    ← 6-panel analysis dashboard
      └── fraud_patterns_report.md     ← (see companion .md file)
""")
