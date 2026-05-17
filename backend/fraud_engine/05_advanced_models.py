# =============================================================
# WEEK 5: ADVANCED FRAUD DETECTION MODELS
# =============================================================
# 📌 What this file does:
#   - Trains 4 advanced ML models: XGBoost, LightGBM, CatBoost, Gradient Boosting
#   - Tunes hyperparameters with Optuna
#   - Compares all models on key metrics
#   - Uses SHAP to explain WHY the model flagged something as fraud
#
# ▶️ How to run:
#   python3 week5_advanced_models.py
# =============================================================

import os
from pathlib import Path

# Keep Matplotlib/font caches inside this project so Code Runner can write them.
os.environ.setdefault("MPLCONFIGDIR", str(Path("outputs/.matplotlib").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("outputs/.cache").resolve()))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, roc_auc_score,
                             roc_curve, precision_recall_curve, average_precision_score)
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import GradientBoostingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
import shap
import optuna
import pickle
import warnings

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

os.makedirs("outputs/.matplotlib", exist_ok=True)
os.makedirs("outputs/.cache", exist_ok=True)
os.makedirs("week5/plots", exist_ok=True)
os.makedirs("week5/models", exist_ok=True)
os.makedirs("week5/reports", exist_ok=True)

print("="*60)
print("🚀 WEEK 5: ADVANCED FRAUD DETECTION MODELS")
print("="*60)

# ── STEP 1: Load & Prepare Data ───────────────────────────────
print("\n📂 Loading dataset...")

for path in ["data/cleaned_dataset.csv",
             "PS_20174392719_1491204439457_log.csv",
             "/Users/snehaarora/Desktop/fraud/PS_20174392719_1491204439457_log.csv"]:
    try:
        df = pd.read_csv(path)
        print(f"✅ Loaded: {path} ({df.shape[0]:,} rows)")
        break
    except FileNotFoundError:
        continue
else:
    print("❌ Dataset not found. Please check the path.")
    exit()

# Rename columns
if 'nameOrig' in df.columns:
    df = df.rename(columns={
        'nameOrig': 'account_from', 'nameDest': 'account_to',
        'oldbalanceOrg': 'old_balance_sender', 'newbalanceOrig': 'new_balance_sender',
        'oldbalanceDest': 'old_balance_receiver', 'newbalanceDest': 'new_balance_receiver',
    })

# Feature Engineering (same as Week 4)
le = LabelEncoder()
df['type_encoded'] = le.fit_transform(df['type'])
df['balance_diff_sender'] = df['old_balance_sender'] - df['new_balance_sender']
df['account_drained'] = (df['new_balance_sender'] == 0).astype(int)
df['zero_start_balance'] = (df['old_balance_sender'] == 0).astype(int)
df['amount_to_balance_ratio'] = df.apply(
    lambda r: r['amount'] / r['old_balance_sender'] if r['old_balance_sender'] > 0 else 0, axis=1)
df['hour_of_day'] = df['step'] % 24
df['is_transfer_or_cashout'] = df['type'].isin(['TRANSFER', 'CASH_OUT']).astype(int)
df['balance_diff_receiver'] = df['new_balance_receiver'] - df['old_balance_receiver']

features = ['type_encoded', 'amount', 'old_balance_sender', 'new_balance_sender',
            'old_balance_receiver', 'new_balance_receiver', 'balance_diff_sender',
            'balance_diff_receiver', 'account_drained', 'zero_start_balance',
            'amount_to_balance_ratio', 'hour_of_day', 'is_transfer_or_cashout',
            'isFlaggedFraud']

# Balance dataset
fraud_df = df[df['isFraud'] == 1]
legit_multiplier = int(os.environ.get("LEGIT_MULTIPLIER", "5"))
legit_df = df[df['isFraud'] == 0]
legit_sample_size = min(len(fraud_df) * legit_multiplier, len(legit_df))
legit_sample = legit_df.sample(n=legit_sample_size, random_state=42)
balanced_df = pd.concat([fraud_df, legit_sample]).sample(frac=1, random_state=42)

X = balanced_df[features]
y = balanced_df['isFraud']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

print(f"✅ Data ready — Train: {len(X_train):,} | Test: {len(X_test):,}")
print(f"   Balanced sample: {len(fraud_df):,} fraud + {legit_sample_size:,} legit")

# ── STEP 2: Train All 4 Models ────────────────────────────────
print("\n" + "="*60)
print("🤖 STEP 2: TRAINING 4 ADVANCED MODELS")
print("="*60)

models = {
    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=50, max_depth=5, learning_rate=0.1, random_state=42),
    "XGBoost": XGBClassifier(
        n_estimators=50, max_depth=5, learning_rate=0.1,
        use_label_encoder=False, eval_metric='logloss',
        random_state=42, n_jobs=-1),
    "LightGBM": LGBMClassifier(
        n_estimators=50, max_depth=5, learning_rate=0.1,
        random_state=42, n_jobs=-1, verbose=-1),
    "CatBoost": CatBoostClassifier(
        iterations=50, depth=5, learning_rate=0.1,
        random_seed=42, verbose=0),
}

results = {}

for name, model in models.items():
    print(f"\n  Training {name}...", end=" ")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    ap  = average_precision_score(y_test, y_prob)
    report = classification_report(y_test, y_pred, output_dict=True)

    results[name] = {
        'model': model,
        'y_pred': y_pred,
        'y_prob': y_prob,
        'auc_roc': auc,
        'avg_precision': ap,
        'precision': report['1']['precision'],
        'recall': report['1']['recall'],
        'f1': report['1']['f1-score'],
    }
    print(f"✅ AUC={auc:.4f} | Precision={report['1']['precision']:.4f} | Recall={report['1']['recall']:.4f}")

# ── STEP 3: Hyperparameter Tuning with Optuna ─────────────────
print("\n" + "="*60)
print("🔧 STEP 3: HYPERPARAMETER TUNING (XGBoost with Optuna)")
print("="*60)
n_trials = int(os.environ.get("OPTUNA_TRIALS", "3"))
print(f"  Running {n_trials} trials with a validation split...")

X_opt_train, X_opt_valid, y_opt_train, y_opt_valid = train_test_split(
    X_train, y_train, test_size=0.25, random_state=42, stratify=y_train
)

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 30, 120),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'use_label_encoder': False,
        'eval_metric': 'logloss',
        'random_state': 42,
        'n_jobs': 1,
    }
    model = XGBClassifier(**params)
    model.fit(X_opt_train, y_opt_train)
    y_prob_valid = model.predict_proba(X_opt_valid)[:, 1]
    return roc_auc_score(y_opt_valid, y_prob_valid)

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

best_params = study.best_params
best_params.update({'use_label_encoder': False, 'eval_metric': 'logloss',
                    'random_state': 42, 'n_jobs': 1})

print(f"\n  ✅ Best parameters found:")
for k, v in study.best_params.items():
    print(f"     {k}: {v}")
print(f"  Best CV AUC: {study.best_value:.4f}")

# Train tuned model
xgb_tuned = XGBClassifier(**best_params)
xgb_tuned.fit(X_train, y_train)
y_pred_tuned = xgb_tuned.predict(X_test)
y_prob_tuned = xgb_tuned.predict_proba(X_test)[:, 1]
auc_tuned = roc_auc_score(y_test, y_prob_tuned)
ap_tuned = average_precision_score(y_test, y_prob_tuned)
report_tuned = classification_report(y_test, y_pred_tuned, output_dict=True)

results['XGBoost (Tuned)'] = {
    'model': xgb_tuned,
    'y_pred': y_pred_tuned,
    'y_prob': y_prob_tuned,
    'auc_roc': auc_tuned,
    'avg_precision': ap_tuned,
    'precision': report_tuned['1']['precision'],
    'recall': report_tuned['1']['recall'],
    'f1': report_tuned['1']['f1-score'],
}
print(f"  Tuned XGBoost AUC: {auc_tuned:.4f}")

# ── STEP 4: Model Comparison ──────────────────────────────────
print("\n" + "="*60)
print("📊 STEP 4: MODEL COMPARISON")
print("="*60)

comparison_df = pd.DataFrame({
    name: {
        'AUC-ROC': f"{r['auc_roc']:.4f}",
        'Avg Precision': f"{r['avg_precision']:.4f}",
        'Precision (Fraud)': f"{r['precision']:.4f}",
        'Recall (Fraud)': f"{r['recall']:.4f}",
        'F1 (Fraud)': f"{r['f1']:.4f}",
    }
    for name, r in results.items()
}).T

print(comparison_df.to_string())

# Save comparison
comparison_df.to_csv('week5/reports/model_comparison.csv')
print("\n  ✅ Comparison saved → week5/reports/model_comparison.csv")

# Best model
best_name = max(results, key=lambda x: results[x]['auc_roc'])
best_result = results[best_name]
print(f"\n  🏆 Best Model: {best_name} (AUC = {best_result['auc_roc']:.4f})")

# ── STEP 5: Visualizations ────────────────────────────────────
print("\n  Generating comparison plots...")

plt.close('all')
fig, axes = plt.subplots(2, 2, figsize=(12, 9))
fig.suptitle('Week 5: Advanced Model Comparison', fontsize=15, fontweight='bold')

colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']

# Plot 1: AUC-ROC Curves
ax1 = axes[0, 0]
for (name, r), color in zip(results.items(), colors):
    fpr, tpr, _ = roc_curve(y_test, r['y_prob'])
    ax1.plot(fpr, tpr, lw=2, color=color, label=f"{name} (AUC={r['auc_roc']:.3f})")
ax1.plot([0,1],[0,1],'k--', lw=1)
ax1.set_title('ROC Curves — All Models')
ax1.set_xlabel('False Positive Rate')
ax1.set_ylabel('True Positive Rate')
ax1.legend(fontsize=8)

# Plot 2: Metric Comparison Bar Chart
ax2 = axes[0, 1]
metric_df = pd.DataFrame({n: {'AUC-ROC': r['auc_roc'], 'Precision': r['precision'],
                               'Recall': r['recall'], 'F1': r['f1']}
                          for n, r in results.items()}).T
metric_df.plot(kind='bar', ax=ax2, colormap='Set2', width=0.8)
ax2.set_title('Model Metrics Comparison')
ax2.set_ylabel('Score')
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=25, ha='right', fontsize=8)
ax2.legend(fontsize=9)
ax2.set_ylim(0, 1.1)

# Plot 3: Precision-Recall Curves
ax3 = axes[1, 0]
for (name, r), color in zip(results.items(), colors):
    prec, rec, _ = precision_recall_curve(y_test, r['y_prob'])
    ax3.plot(rec, prec, lw=2, color=color, label=f"{name} (AP={r['avg_precision']:.3f})")
ax3.set_title('Precision-Recall Curves')
ax3.set_xlabel('Recall')
ax3.set_ylabel('Precision')
ax3.legend(fontsize=8)

# Plot 4: Feature Importance (best model)
ax4 = axes[1, 1]
best_model = best_result['model']
if hasattr(best_model, 'feature_importances_'):
    imp = pd.Series(best_model.feature_importances_, index=features).sort_values(ascending=True)
    imp.plot(kind='barh', ax=ax4, color='steelblue')
    ax4.set_title(f'Feature Importance\n({best_name})')
    ax4.set_xlabel('Importance Score')

plt.tight_layout()
plt.savefig('week5/plots/model_comparison.png', dpi=100, bbox_inches='tight')
plt.close()
print("  ✅ Plot saved → week5/plots/model_comparison.png")

# ── STEP 6: SHAP Explainability ───────────────────────────────
print("\n" + "="*60)
print("🔍 STEP 6: SHAP EXPLAINABILITY")
print("="*60)
print("  📌 SHAP tells us WHY the model flagged a transaction as fraud")
print("  Computing SHAP values (may take 1-2 minutes)...")

# Use a sample for SHAP (full dataset takes too long)
X_shap_sample = X_test.sample(min(200, len(X_test)), random_state=42)

explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_shap_sample)

# Handle different SHAP output formats
if isinstance(shap_values, list):
    sv = shap_values[1]  # Class 1 (fraud) SHAP values
else:
    sv = shap_values

# Plot 1: SHAP Summary (overall feature importance)
plt.figure(figsize=(10, 7))
shap.summary_plot(sv, X_shap_sample, feature_names=features,
                  plot_type='bar', show=False)
plt.title(f'SHAP Feature Importance — {best_name}', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('week5/plots/shap_feature_importance.png', dpi=100, bbox_inches='tight')
plt.close()
print("  ✅ SHAP importance plot saved → week5/plots/shap_feature_importance.png")

# Plot 2: SHAP Beeswarm (how each feature affects fraud prediction)
plt.figure(figsize=(10, 7))
shap.summary_plot(sv, X_shap_sample, feature_names=features, show=False)
plt.title(f'SHAP Beeswarm Plot — {best_name}\n(Red = pushes toward fraud, Blue = pushes away)',
          fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig('week5/plots/shap_beeswarm.png', dpi=100, bbox_inches='tight')
plt.close()
print("  ✅ SHAP beeswarm plot saved → week5/plots/shap_beeswarm.png")

# Case Study: Explain one fraud prediction
print("\n  📋 Case Study: Explaining ONE fraud prediction")
fraud_indices = X_shap_sample[y_test.loc[X_shap_sample.index] == 1].index
if len(fraud_indices) > 0:
    idx = fraud_indices[0]
    case = X_shap_sample.loc[idx]
    case_shap = sv[X_shap_sample.index.get_loc(idx)]
    print(f"\n  Transaction details:")
    print(f"    Type:          {le.classes_[int(case['type_encoded'])]}")
    print(f"    Amount:        ₹{case['amount']:,.2f}")
    print(f"    Old Balance:   ₹{case['old_balance_sender']:,.2f}")
    print(f"    New Balance:   ₹{case['new_balance_sender']:,.2f}")
    print(f"    Acct Drained:  {'YES' if case['account_drained'] == 1 else 'NO'}")
    print(f"\n  Top factors pushing toward FRAUD prediction:")
    shap_series = pd.Series(case_shap, index=features).sort_values(ascending=False)
    for feat, val in shap_series.head(5).items():
        direction = "→ FRAUD" if val > 0 else "→ LEGIT"
        print(f"    {feat:35s}: {val:+.4f}  {direction}")

# ── STEP 7: Save Best Model ───────────────────────────────────
with open('week5/models/best_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

with open('week5/models/label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

with open('week5/models/feature_list.pkl', 'wb') as f:
    pickle.dump(features, f)

print("\n" + "="*60)
print("🎉 WEEK 5 COMPLETE!")
print("="*60)
print(f"""
Best Model: {best_name}
AUC-ROC:    {best_result['auc_roc']:.4f}
Precision:  {best_result['precision']:.4f}
Recall:     {best_result['recall']:.4f}
F1-Score:   {best_result['f1']:.4f}

Files created:
  📁 week5/models/best_model.pkl
  📁 week5/models/label_encoder.pkl
  📁 week5/models/feature_list.pkl
  📁 week5/plots/model_comparison.png
  📁 week5/plots/shap_feature_importance.png
  📁 week5/plots/shap_beeswarm.png
  📁 week5/reports/model_comparison.csv

Next: Run week6_api.py to deploy as a REST API!
""")
