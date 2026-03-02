import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

DATA_DIR = "dataset_reg"

def evaluate(target_name, name, model, X_train, y_train, X_test, y_test):
    # Train
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Calculate Error
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return {
        "Target": target_name,
        "Model": name,
        "MAE": mae,
        "RMSE": rmse,
        "Train Time (s)": train_time
    }

def plot_comparison(df, target_name, unit, filename):
    """Generates the Error Comparison Bar Chart for a specific target"""
    # Filter for the specific target (Energy or Latency)
    df_sub = df[df['Target'] == target_name]
    
    models = df_sub['Model']
    mae_scores = df_sub['MAE']
    rmse_scores = df_sub['RMSE']
    
    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    rects1 = ax.bar(x - width/2, mae_scores, width, label=f'MAE ({unit})', color='#4c72b0', alpha=0.9, edgecolor='black')
    rects2 = ax.bar(x + width/2, rmse_scores, width, label=f'RMSE ({unit})', color='#c44e52', alpha=0.9, edgecolor='black')

    ax.set_ylabel(f'Error ({unit}) - Lower is Better')
    ax.set_title(f'{target_name} Prediction Accuracy\n(HGBDT vs Baselines)')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    # Label bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"[OK] Saved plot: {filename}")

def main():
    print("Loading data...")
    try:
        X_train = np.load(os.path.join(DATA_DIR, "X_train.npy"))
        X_test  = np.load(os.path.join(DATA_DIR, "X_test.npy"))
        
        # Energy Targets
        yE_train = np.load(os.path.join(DATA_DIR, "y_energy_train.npy"))
        yE_test  = np.load(os.path.join(DATA_DIR, "y_energy_test.npy"))
        
        # Latency Targets
        yL_train = np.load(os.path.join(DATA_DIR, "y_latency_train.npy"))
        yL_test  = np.load(os.path.join(DATA_DIR, "y_latency_test.npy"))
        
    except FileNotFoundError:
        print("Error: Dataset not found. Please run '2. build_dataset_regression.py' first.")
        return

    print(f"Training on {len(X_train)} samples, Testing on {len(X_test)} samples...\n")

    # Define Models
    # Note: We create fresh instances for each target to avoid fitting on top of each other
    model_defs = [
        ("Linear Regression", LinearRegression()),
        ("Random Forest", RandomForestRegressor(n_estimators=100, random_state=42)),
        ("HGBDT (Ours)", HistGradientBoostingRegressor(learning_rate=0.05, max_depth=8, random_state=42))
    ]

    results = []

    # --- 1. Evaluate Energy ---
    print("--- Evaluating Energy Models ---")
    for name, clf in model_defs:
        # Clone model (re-instantiate) to be safe
        from sklearn.base import clone
        clf = clone(clf)
        res = evaluate("Energy", name, clf, X_train, yE_train, X_test, yE_test)
        results.append(res)

    # --- 2. Evaluate Latency ---
    print("--- Evaluating Latency Models ---")
    for name, clf in model_defs:
        from sklearn.base import clone
        clf = clone(clf)
        res = evaluate("Latency", name, clf, X_train, yL_train, X_test, yL_test)
        results.append(res)

    # Create DataFrame
    df_res = pd.DataFrame(results)

    # Print Table
    print("\n" + "="*60)
    print("      MODEL COMPARISON RESULTS (Energy & Latency)      ")
    print("="*60)
    print(df_res.to_string(index=False))
    print("="*60)
    
    # Save Table
    df_res.to_csv("model_comparison_full.csv", index=False)
    print("\n[OK] Saved results to model_comparison_full.csv")

    # Generate Plots
    print("\nGenerating Plots...")
    plot_comparison(df_res, "Energy", "Joules", "fig_benchmark_energy.png")
    plot_comparison(df_res, "Latency", "ms", "fig_benchmark_latency.png")

if __name__ == "__main__":
    main()