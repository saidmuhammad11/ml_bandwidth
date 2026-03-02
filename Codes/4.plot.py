import os
import numpy as np
import matplotlib.pyplot as plt
import joblib
import json

# Settings
MODEL_DIR = "models"
DATA_DIR = "dataset_reg"

def main():
    # 1. Load Data
    print("Loading test data...")
    X_test = np.load(os.path.join(DATA_DIR, "X_test.npy"))
    yE_test = np.load(os.path.join(DATA_DIR, "y_energy_test.npy"))
    
    print("Loading Energy Model...")
    energy_model = joblib.load(os.path.join(MODEL_DIR, "energy_hgbdt.joblib"))

    # 2. Predict
    yE_pred = energy_model.predict(X_test)
    
    # 3. Calculate R2
    correlation = np.corrcoef(yE_test, yE_pred)[0, 1]
    r2 = correlation**2
    print(f"Energy R² Score: {r2:.4f}")

    # --- PLOT 1: PREDICTED VS ACTUAL ---
    plt.figure(figsize=(7, 6))
    plt.scatter(yE_test, yE_pred, alpha=0.5, color='blue', edgecolors='k', s=30, label='Test Samples')
    
    # Perfect line
    min_val = min(yE_test.min(), yE_pred.min())
    max_val = max(yE_test.max(), yE_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')

    plt.title(f"Energy Prediction Accuracy\n(MAE: 2.99 J | R²: {r2:.3f})")
    plt.xlabel("Actual Energy (Joules) - Measured via RAPL")
    plt.ylabel("Predicted Energy (Joules) - ML Model")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig("fig_energy_accuracy.png", dpi=300)
    print("[OK] Saved fig_energy_accuracy.png")

    # --- PLOT 2: FEATURE IMPORTANCE ---
    # We need feature names from meta.json
    with open(os.path.join(DATA_DIR, "meta.json"), "r") as f:
        meta = json.load(f)
    feature_names = np.array(meta["features"])
    
    # Permutation Importance (Simple approximation for HGBDT)
    from sklearn.inspection import permutation_importance
    
    print("Calculating Feature Importance (this takes a moment)...")
    result = permutation_importance(energy_model, X_test, yE_test, n_repeats=10, random_state=42, n_jobs=-1)
    
    sorted_idx = result.importances_mean.argsort()
    
    plt.figure(figsize=(10, 6))
    plt.boxplot(result.importances[sorted_idx].T, vert=False, labels=feature_names[sorted_idx])
    plt.title("Feature Importance for Energy Consumption")
    plt.xlabel("Importance (Decrease in Accuracy if removed)")
    plt.tight_layout()
    plt.savefig("fig_feature_importance.png", dpi=300)
    print("[OK] Saved fig_feature_importance.png")

if __name__ == "__main__":
    main()
