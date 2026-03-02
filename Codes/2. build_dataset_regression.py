import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split

INPUT_CSV = "prepared.csv"
OUT_DIR = "dataset_reg"

# Features expected in the CSV
BASE_FEATURES = [
    "mem_limit_mb",
    "cold_start",
    "concurrency",
    "queue_delay_ms",
    "cpu_time_ms",
    "peak_rss_mb",
    "rss_mb",
    "io_read_bytes",
    "io_write_bytes",
]

TARGET_LATENCY = "duration_ms"
TARGET_ENERGY = "energy_joules"
GROUP_COL = "run_id"
WORKLOAD_COL = "workload"

def main():
    df = pd.read_csv(INPUT_CSV)
    print(f"Total rows read: {len(df)}")

    # 1. FIX: Handle Boolean "True"/"False" strings safely
    # Map string variants to 1/0 immediately
    bool_map = {
        "True": 1, "False": 0, 
        "true": 1, "false": 0, 
        True: 1, False: 0,
        1: 1, 0: 0
    }
    if "cold_start" in df.columns:
        df["cold_start"] = df["cold_start"].map(bool_map)

    # 2. Check for missing columns
    required = set(BASE_FEATURES + [TARGET_LATENCY, TARGET_ENERGY, GROUP_COL, WORKLOAD_COL])
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # 3. Convert ONLY strictly numeric columns (exclude cold_start which is already fixed)
    numeric_cols = [c for c in BASE_FEATURES if c != "cold_start"] + [TARGET_LATENCY, TARGET_ENERGY]
    
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # 4. Debug: Check what is becoming NaN
    # If rows are still dropped, uncomment lines below to see WHY
    # print(df[df.isna().any(axis=1)])

    # 5. Clean Data
    initial_count = len(df)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=BASE_FEATURES + [TARGET_LATENCY, TARGET_ENERGY, GROUP_COL, WORKLOAD_COL])
    
    # Filter out bad latency
    df = df[df[TARGET_LATENCY] > 0]

    print(f"Rows after cleaning: {len(df)} (Dropped {initial_count - len(df)})")

    if len(df) == 0:
        raise ValueError("Dataframe is empty! Check if columns like 'energy_joules' or 'cpu_time_ms' are all NaNs.")

    # ---- Feature Engineering ----
    eps = 1e-9
    df["cold_start"] = df["cold_start"].astype(int)
    df["rss_ratio"] = df["peak_rss_mb"] / (df["mem_limit_mb"] + eps)
    df["cpu_per_mem"] = df["cpu_time_ms"] / (df["mem_limit_mb"] + eps)
    df["log_mem"] = np.log1p(df["mem_limit_mb"].astype(float))

    # One-hot encode workload
    workload_dummies = pd.get_dummies(df[WORKLOAD_COL].astype(str), prefix="workload", prefix_sep="__")
    
    # Build final feature set
    feature_df = df[BASE_FEATURES].copy()
    feature_df["rss_ratio"] = df["rss_ratio"]
    feature_df["cpu_per_mem"] = df["cpu_per_mem"]
    feature_df["log_mem"] = df["log_mem"]
    
    workload_dummies = workload_dummies.reindex(sorted(workload_dummies.columns), axis=1)
    feature_df = pd.concat([feature_df, workload_dummies], axis=1)

    FEATURES = feature_df.columns.tolist()

    # Split Data
    X = feature_df.astype(float).values
    y_latency = df[TARGET_LATENCY].astype(float).values
    y_energy = df[TARGET_ENERGY].astype(float).values
    groups = df[GROUP_COL].astype(str).values

    idx = np.arange(len(df))
    unique_groups = np.unique(groups)

    if len(unique_groups) >= 2:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(splitter.split(X, y_latency, groups))
    else:
        # Fallback if only 1 run_id exists
        print("Warning: Only 1 Group/Run ID found. Using random split instead of group split.")
        train_idx, test_idx = train_test_split(idx, test_size=0.2, random_state=42)

    X_train, X_test = X[train_idx], X[test_idx]
    yL_train, yL_test = y_latency[train_idx], y_latency[test_idx]
    yE_train, yE_test = y_energy[train_idx], y_energy[test_idx]

    os.makedirs(OUT_DIR, exist_ok=True)
    np.save(os.path.join(OUT_DIR, "X_train.npy"), X_train)
    np.save(os.path.join(OUT_DIR, "X_test.npy"), X_test)
    np.save(os.path.join(OUT_DIR, "y_latency_train.npy"), yL_train)
    np.save(os.path.join(OUT_DIR, "y_latency_test.npy"), yL_test)
    np.save(os.path.join(OUT_DIR, "y_energy_train.npy"), yE_train)
    np.save(os.path.join(OUT_DIR, "y_energy_test.npy"), yE_test)

    # Save Meta
    meta = {
        "features": FEATURES,
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "workload_onehot": workload_dummies.columns.tolist()
    }
    with open(os.path.join(OUT_DIR, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n[OK] Dataset built. Train size: {len(train_idx)}, Test size: {len(test_idx)}")

if __name__ == "__main__":
    main()