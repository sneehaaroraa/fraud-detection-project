# =============================================================
# WEEK 1: DATA EXPLORATION — Fraud Detection Project
# =============================================================
# 📌 What this file does:
#   - Loads the PaySim dataset
#   - Inspects its structure
#   - Cleans it (removes nulls, fixes types)
#   - Does Exploratory Data Analysis (EDA) with graphs
#   - Saves a cleaned version of the dataset
#
# ▶️ How to run:
#   Open this in Jupyter Notebook OR run: python week1_data_exploration.py
# =============================================================

# ── STEP 0: Import Libraries ─────────────────────────────────
# Think of libraries as toolboxes. We import them once at the top.

import os
import sys
from pathlib import Path

# Keep Matplotlib/font caches inside this project so Code Runner can write them.
os.environ.setdefault("MPLCONFIGDIR", str(Path("outputs/.matplotlib").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("outputs/.cache").resolve()))

import pandas as pd                   # For loading and manipulating data (like Excel in Python)
import matplotlib.pyplot as plt       # For drawing graphs
import seaborn as sns                 # For prettier graphs

# Make output folders if they don't exist
os.makedirs("outputs/plots", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("outputs/.matplotlib", exist_ok=True)
os.makedirs("outputs/.cache", exist_ok=True)

print("✅ Libraries imported successfully!")

# ── STEP 1: Load the Dataset ──────────────────────────────────
# 📌 Change the path below to wherever your CSV file is saved.
#    Example: "C:/Users/YourName/Downloads/PS_20174392719_1491204439457_log.csv"

DEFAULT_DATA_PATH = "dataset.csv"


def find_dataset_path():
    """Return the dataset path from CLI/env/default, or auto-detect a CSV file."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1])

    if os.environ.get("DATA_PATH"):
        return Path(os.environ["DATA_PATH"])

    default_path = Path(DEFAULT_DATA_PATH)
    if default_path.exists():
        return default_path

    csv_files = []
    for folder in [Path("."), Path("data"), Path("dataset"), Path("datasets")]:
        if folder.exists():
            csv_files.extend(folder.glob("*.csv"))

    # Ignore outputs created by this script.
    csv_files = [
        path for path in csv_files
        if "outputs" not in path.parts and path.name != "cleaned_dataset.csv"
    ]

    return csv_files[0] if len(csv_files) == 1 else default_path


DATA_PATH = find_dataset_path()

print(f"\n📂 Loading dataset from: {DATA_PATH}")
if not DATA_PATH.exists():
    print("\n❌ Dataset file not found.")
    print("Put your PaySim CSV in this folder as 'dataset.csv', or run:")
    print("   python3 week1_data_exploration.py /path/to/your_dataset.csv")
    print("\nExpected columns include:")
    print("   step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig,")
    print("   nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud")
    sys.exit(1)

df = pd.read_csv(DATA_PATH)
print(f"✅ Dataset loaded! Shape: {df.shape[0]} rows × {df.shape[1]} columns")

required_columns = {
    'step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig',
    'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud', 'isFlaggedFraud'
}
missing_columns = sorted(required_columns - set(df.columns))
if missing_columns:
    print("\n❌ This CSV does not look like the PaySim fraud dataset.")
    print("Missing columns:")
    for column in missing_columns:
        print(f"   - {column}")
    sys.exit(1)

# ── STEP 2: Basic Inspection ──────────────────────────────────
# Let's peek at what the data looks like

print("\n" + "="*60)
print("📋 FIRST 5 ROWS (df.head())")
print("="*60)
print(df.head())

print("\n" + "="*60)
print("📊 COLUMN INFO (df.info()) — shows data types and nulls")
print("="*60)
df.info()

print("\n" + "="*60)
print("📈 STATISTICAL SUMMARY (df.describe())")
print("="*60)
print(df.describe())

# ── STEP 3: Check for Missing Values ──────────────────────────
print("\n" + "="*60)
print("🔍 MISSING VALUES PER COLUMN")
print("="*60)
missing = df.isnull().sum()
print(missing[missing > 0] if missing.sum() > 0 else "✅ No missing values found!")

# ── STEP 4: Understand the Columns ────────────────────────────
# The PaySim dataset has these important columns:
#   step          → time unit (1 step = 1 hour)
#   type          → transaction type (TRANSFER, CASH_OUT, etc.)
#   amount        → money moved
#   nameOrig      → sender account
#   nameDest      → receiver account
#   oldbalanceOrg → sender balance BEFORE transaction
#   newbalanceOrig→ sender balance AFTER transaction
#   isFraud       → 1 = fraud, 0 = not fraud  ← our TARGET column!
#   isFlaggedFraud→ flagged by the bank's own system

print("\n" + "="*60)
print("🏷️  UNIQUE TRANSACTION TYPES")
print("="*60)
print(df['type'].value_counts())

print("\n" + "="*60)
print("🚨 FRAUD vs NON-FRAUD COUNT")
print("="*60)
fraud_counts = df['isFraud'].value_counts()
print(fraud_counts)
fraud_pct = df['isFraud'].mean() * 100
print(f"\n⚠️  Fraud rate: {fraud_pct:.4f}% of all transactions")

# ── STEP 5: Exploratory Data Analysis (EDA) ───────────────────
# Now we make graphs to understand patterns visually

print("\n📊 Generating EDA plots...")

# --- Plot 1: Transaction Type Distribution ---
plt.figure(figsize=(9, 5))
sns.countplot(data=df, x='type', palette='Set2',
              order=df['type'].value_counts().index)
plt.title('📊 Plot 1: Transaction Type Distribution', fontsize=14, fontweight='bold')
plt.xlabel('Transaction Type')
plt.ylabel('Count')
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig('outputs/plots/plot1_transaction_types.png', dpi=150)
plt.close()
print("  ✅ Plot 1 saved: Transaction Type Distribution")

# --- Plot 2: Fraud vs Non-Fraud by Transaction Type ---
plt.figure(figsize=(9, 5))
fraud_by_type = df.groupby('type')['isFraud'].mean().reset_index()
fraud_by_type['isFraud'] = fraud_by_type['isFraud'] * 100
sns.barplot(data=fraud_by_type, x='type', y='isFraud', palette='Reds_d')
plt.title('📊 Plot 2: Fraud Rate (%) by Transaction Type', fontsize=14, fontweight='bold')
plt.xlabel('Transaction Type')
plt.ylabel('Fraud Rate (%)')
plt.tight_layout()
plt.savefig('outputs/plots/plot2_fraud_rate_by_type.png', dpi=150)
plt.close()
print("  ✅ Plot 2 saved: Fraud Rate by Transaction Type")

# --- Plot 3: Transaction Amount Distribution (Fraud vs Non-Fraud) ---
plt.figure(figsize=(10, 5))
df_plot = df[df['amount'] < 1_000_000]  # Remove extreme outliers for better view
sns.histplot(data=df_plot, x='amount', hue='isFraud',
             bins=60, palette={0: 'steelblue', 1: 'crimson'}, log_scale=(False, True))
plt.title('📊 Plot 3: Transaction Amount Distribution\n(Red = Fraud, Blue = Legit)',
          fontsize=13, fontweight='bold')
plt.xlabel('Amount')
plt.ylabel('Count (log scale)')
plt.tight_layout()
plt.savefig('outputs/plots/plot3_amount_distribution.png', dpi=150)
plt.close()
print("  ✅ Plot 3 saved: Amount Distribution")

# --- Plot 4: Fraud Count Over Time (by step) ---
plt.figure(figsize=(12, 4))
fraud_over_time = df[df['isFraud'] == 1].groupby('step').size()
plt.plot(fraud_over_time.index, fraud_over_time.values, color='crimson', linewidth=1)
plt.fill_between(fraud_over_time.index, fraud_over_time.values, alpha=0.3, color='crimson')
plt.title('📊 Plot 4: Fraud Transactions Over Time (by step/hour)', fontsize=13, fontweight='bold')
plt.xlabel('Step (1 step = 1 hour)')
plt.ylabel('Number of Fraud Cases')
plt.tight_layout()
plt.savefig('outputs/plots/plot4_fraud_over_time.png', dpi=150)
plt.close()
print("  ✅ Plot 4 saved: Fraud Over Time")

# --- Plot 5: Old Balance vs New Balance for Fraud Cases ---
plt.figure(figsize=(8, 5))
fraud_df = df[df['isFraud'] == 1].sample(min(500, len(df[df['isFraud']==1])), random_state=42)
plt.scatter(fraud_df['oldbalanceOrg'], fraud_df['newbalanceOrig'],
            alpha=0.4, color='crimson', s=15)
plt.title('📊 Plot 5: Old vs New Balance (Fraud Cases)\nNote: Many fraud cases drain account to 0',
          fontsize=12, fontweight='bold')
plt.xlabel('Old Balance (Before Transaction)')
plt.ylabel('New Balance (After Transaction)')
plt.tight_layout()
plt.savefig('outputs/plots/plot5_balance_fraud.png', dpi=150)
plt.close()
print("  ✅ Plot 5 saved: Balance Pattern in Fraud")

# ── STEP 6: Key Fraud Patterns ────────────────────────────────
print("\n" + "="*60)
print("🔍 KEY FRAUD PATTERN FINDINGS")
print("="*60)

# Pattern 1: Only TRANSFER and CASH_OUT have fraud
fraud_types = df[df['isFraud'] == 1]['type'].value_counts()
print("\n1️⃣  Fraud only occurs in these transaction types:")
print(fraud_types)

# Pattern 2: Zero balance after transaction
zero_balance_fraud = df[(df['isFraud'] == 1) & (df['newbalanceOrig'] == 0)].shape[0]
total_fraud = df[df['isFraud'] == 1].shape[0]
if total_fraud > 0:
    print(f"\n2️⃣  Fraud cases where account drained to 0: {zero_balance_fraud}/{total_fraud} "
          f"({zero_balance_fraud/total_fraud*100:.1f}%)")
else:
    print("\n2️⃣  No fraud cases found in this dataset.")

# Pattern 3: High-value frauds
high_value_fraud = df[(df['isFraud'] == 1) & (df['amount'] > 100_000)].shape[0]
if total_fraud > 0:
    print(f"\n3️⃣  Fraud cases with amount > ₹100,000: {high_value_fraud}/{total_fraud} "
          f"({high_value_fraud/total_fraud*100:.1f}%)")
else:
    print("\n3️⃣  No high-value fraud percentage to calculate.")

# Pattern 4: Top 10 most targeted destination accounts
print("\n4️⃣  Top 10 most targeted destination accounts (fraud only):")
top_targets = df[df['isFraud'] == 1]['nameDest'].value_counts().head(10)
print(top_targets)

# ── STEP 7: Save Cleaned Dataset ──────────────────────────────
print("\n" + "="*60)
print("💾 SAVING CLEANED DATASET")
print("="*60)

# Convert step to simulated datetime (step 1 = Jan 1, 2023 00:00)
df['timestamp'] = pd.to_datetime('2023-01-01') + pd.to_timedelta(df['step'], unit='h')

# Rename columns to be more readable
df_cleaned = df.rename(columns={
    'nameOrig': 'account_from',
    'nameDest': 'account_to',
    'oldbalanceOrg': 'old_balance_sender',
    'newbalanceOrig': 'new_balance_sender',
    'oldbalanceDest': 'old_balance_receiver',
    'newbalanceDest': 'new_balance_receiver',
})

# Save to CSV
df_cleaned.to_csv('data/cleaned_dataset.csv', index=False)
print("✅ Cleaned dataset saved to: data/cleaned_dataset.csv")
print(f"   Shape: {df_cleaned.shape[0]} rows × {df_cleaned.shape[1]} columns")

print("\n" + "="*60)
print("🎉 WEEK 1 COMPLETE! All outputs saved in:")
print("   📁 data/cleaned_dataset.csv")
print("   📁 outputs/plots/ (6 PNG charts)")
print("="*60)

if missing.sum() > 0:
    print(missing)
else: 
    print("No missing values")

# -----------------------------
# CORRELATION HEATMAP
# -----------------------------
numeric_df = df.select_dtypes(include=['number'])

plt.figure(figsize=(12, 8))

sns.heatmap(
    numeric_df.corr(),
    cmap='coolwarm',
    annot=False
)

plt.title("Correlation Heatmap")

plt.tight_layout()
plt.savefig('outputs/plots/plot6_correlation_heatmap.png', dpi=150)
plt.close()
print("  ✅ Plot 6 saved: Correlation Heatmap")

# -----------------------------
# FINAL MESSAGE
# -----------------------------
print("\n✅Data Exploration Completed Successfully!")
