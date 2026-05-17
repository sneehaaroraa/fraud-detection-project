# =============================================================
# WEEK 4: BASELINE FRAUD DETECTION MODEL
# =============================================================
# 📌 What this file does:
#   - Loads the cleaned dataset
#   - Prepares features for machine learning
#   - Handles the imbalanced dataset problem
#   - Trains a baseline Random Forest model
#   - Evaluates it with proper fraud metrics
#
# ▶️ How to run:
#   python3 week4_baseline_model.py
# =============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, roc_curve, precision_recall_curve)
from sklearn.preprocessing import LabelEncoder
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs("week4/plots", exist_ok=True)
os.makedirs("week4/models", exist_ok=True)

print("="*60)
print("🚀 WEEK 4: BASELINE FRAUD DETECTION MODEL")
print("="*60)

# ── STEP 1: Load Dataset ──────────────────────────────────────
print("\n📂 Loading dataset...")

# Try loading cleaned dataset first, then raw
for path in ["data/cleaned_dataset.csv",
             "PS_20174392719_1491204439457_log.csv",
             "/Users/snehaarora/Desktop/fraud/PS_20174392719_1491204439457_log.csv"]:
    try:
        df = pd.read_csv(path)
        print(f"✅ Loaded: {path} — {df.shape[0]:,} rows")
        break
    except FileNotFoundError:
        continue
else:
    print("❌ Dataset not found. Please update the path.")
    exit()

# ── STEP 2: Feature Engineering ───────────────────────────────
# 📌 Machine learning needs NUMBERS, not text.
#    We create useful numeric features from the raw columns.

print("\n" + "="*60)
print("⚙️  STEP 2: FEATURE ENGINEERING")
print("="*60)

# Rename columns if they haven't been renamed yet
if 'nameOrig' in df.columns:
    df = df.rename(columns={
        'nameOrig': 'account_from',
        'nameDest': 'account_to',
        'oldbalanceOrg': 'old_balance_sender',
        'newbalanceOrig': 'new_balance_sender',
        'oldbalanceDest': 'old_balance_receiver',
        'newbalanceDest': 'new_balance_receiver',
    })

# Feature 1: Encode transaction type as a number
# (ML models can't read text like "TRANSFER")
le = LabelEncoder()
df['type_encoded'] = le.fit_transform(df['type'])
print(f"  Type encoding: {dict(zip(le.classes_, le.transform(le.classes_)))}")

# Feature 2: Balance difference for sender
# How much did the sender's balance change?
df['balance_diff_sender'] = df['old_balance_sender'] - df['new_balance_sender']

# Feature 3: Was the account completely drained?
# This was our #1 fraud signal from Week 3!
df['account_drained'] = (df['new_balance_sender'] == 0).astype(int)

# Feature 4: Was the sender's starting balance zero?
df['zero_start_balance'] = (df['old_balance_sender'] == 0).astype(int)

# Feature 5: Amount relative to old balance
# A transfer of 100% of your balance is suspicious
df['amount_to_balance_ratio'] = df.apply(
    lambda r: r['amount'] / r['old_balance_sender']
    if r['old_balance_sender'] > 0 else 0, axis=1
)

# Feature 6: Hour of day (from step)
df['hour_of_day'] = df['step'] % 24

# Feature 7: Is it a TRANSFER or CASH_OUT? (only these have fraud)
df['is_transfer_or_cashout'] = df['type'].isin(['TRANSFER', 'CASH_OUT']).astype(int)

print("  ✅ Features created:")
features = ['type_encoded', 'amount', 'old_balance_sender', 'new_balance_sender',
            'old_balance_receiver', 'new_balance_receiver', 'balance_diff_sender',
            'account_drained', 'zero_start_balance', 'amount_to_balance_ratio',
            'hour_of_day', 'is_transfer_or_cashout', 'isFlaggedFraud']

for f in features:
    print(f"    • {f}")

# ── STEP 3: Prepare X and y ───────────────────────────────────
print("\n" + "="*60)
print("📊 STEP 3: PREPARING TRAINING DATA")
print("="*60)

# X = features (what the model learns from)
# y = target (what the model is trying to predict)
X = df[features]
y = df['isFraud']

print(f"  Features (X): {X.shape[1]} columns, {X.shape[0]:,} rows")
print(f"  Target (y): {y.value_counts().to_dict()}")
print(f"  Fraud rate: {y.mean()*100:.4f}%")

# ── STEP 4: Handle Imbalanced Data ────────────────────────────
# 📌 IMPORTANT CONCEPT:
#    Only 0.13% of transactions are fraud.
#    If we train naively, the model just predicts "not fraud" for everything
#    and gets 99.87% accuracy — but catches ZERO fraud!
#    Solution: undersample the majority class (non-fraud)

print("\n" + "="*60)
print("⚖️  STEP 4: HANDLING CLASS IMBALANCE")
print("="*60)

fraud_df = df[df['isFraud'] == 1]
legit_df = df[df['isFraud'] == 0]

# Undersample: take same number of legit as fraud (×10 for better coverage)
n_fraud = len(fraud_df)
n_sample = min(n_fraud * 10, len(legit_df))

legit_sample = legit_df.sample(n=n_sample, random_state=42)
balanced_df = pd.concat([fraud_df, legit_sample]).sample(frac=1, random_state=42)

X_bal = balanced_df[features]
y_bal = balanced_df['isFraud']

print(f"  Original: {len(fraud_df):,} fraud vs {len(legit_df):,} legit")
print(f"  Balanced: {y_bal.sum():,} fraud vs {(y_bal==0).sum():,} legit")
print(f"  New fraud rate: {y_bal.mean()*100:.1f}%")

# ── STEP 5: Train/Test Split ──────────────────────────────────
# 80% of data for training, 20% for testing
X_train, X_test, y_train, y_test = train_test_split(
    X_bal, y_bal, test_size=0.2, random_state=42, stratify=y_bal
)
print(f"\n  Training set: {len(X_train):,} samples")
print(f"  Test set:     {len(X_test):,} samples")

# ── STEP 6: Train Random Forest ───────────────────────────────
print("\n" + "="*60)
print("🌲 STEP 5: TRAINING RANDOM FOREST MODEL")
print("="*60)
print("  This may take 1-2 minutes...")

rf_model = RandomForestClassifier(
    n_estimators=100,      # 100 decision trees
    max_depth=10,          # Each tree goes 10 levels deep
    random_state=42,
    n_jobs=-1,             # Use all CPU cores
    class_weight='balanced'
)

rf_model.fit(X_train, y_train)
print("  ✅ Model trained!")

# ── STEP 7: Evaluate ──────────────────────────────────────────
print("\n" + "="*60)
print("📈 STEP 6: MODEL EVALUATION")
print("="*60)

y_pred = rf_model.predict(X_test)
y_prob = rf_model.predict_proba(X_test)[:, 1]

print("\n  Classification Report:")
print(classification_report(y_test, y_pred, target_names=['Legit', 'Fraud']))

auc = roc_auc_score(y_test, y_prob)
print(f"  AUC-ROC Score: {auc:.4f}")
print("""
  📌 How to read these metrics:
     Precision = Of all transactions flagged as fraud, how many were actually fraud?
     Recall    = Of all actual fraud cases, how many did we catch?
     F1-Score  = Balance between Precision and Recall
     AUC-ROC   = Overall model quality (1.0 = perfect, 0.5 = random guessing)
""")

# ── STEP 8: Plots ─────────────────────────────────────────────
print("  Generating evaluation plots...")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle('Week 4: Random Forest Baseline Model Results', fontsize=14, fontweight='bold')

# Plot 1: Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
            xticklabels=['Legit', 'Fraud'], yticklabels=['Legit', 'Fraud'])
axes[0].set_title('Confusion Matrix')
axes[0].set_ylabel('Actual')
axes[0].set_xlabel('Predicted')

# Plot 2: ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_prob)
axes[1].plot(fpr, tpr, color='crimson', lw=2, label=f'AUC = {auc:.3f}')
axes[1].plot([0,1], [0,1], 'k--', lw=1)
axes[1].set_title('ROC Curve')
axes[1].set_xlabel('False Positive Rate')
axes[1].set_ylabel('True Positive Rate (Recall)')
axes[1].legend()

# Plot 3: Feature Importance
importances = pd.Series(rf_model.feature_importances_, index=features).sort_values(ascending=True)
importances.plot(kind='barh', ax=axes[2], color='steelblue')
axes[2].set_title('Feature Importance')
axes[2].set_xlabel('Importance Score')

plt.tight_layout()
plt.savefig('week4/plots/baseline_model_results.png', dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ Plot saved → week4/plots/baseline_model_results.png")

# Save model
import pickle
with open('week4/models/random_forest_baseline.pkl', 'wb') as f:
    pickle.dump(rf_model, f)
print("  ✅ Model saved → week4/models/random_forest_baseline.pkl")

print("\n" + "="*60)
print("🎉 WEEK 4 COMPLETE!")
print("="*60)
print(f"""
Results Summary:
  Model: Random Forest (100 trees)
  AUC-ROC: {auc:.4f}
  
Files created:
  📁 week4/plots/baseline_model_results.png
  📁 week4/models/random_forest_baseline.pkl
  
Next: Run week5_advanced_models.py for XGBoost + SHAP
""")
