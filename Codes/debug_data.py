import pandas as pd
import numpy as np

# Load the data (reading from current folder)
try:
    df = pd.read_csv("prepared.csv")
    print(f"Total Rows: {len(df)}")
except FileNotFoundError:
    print("ERROR: prepared.csv not found in current folder!")
    exit()

# Check for "None", Empty, or NaN values
print("\n--- Missing Value Count (per column) ---")
print(df.isna().sum())

print("\n--- First 3 Rows of Data ---")
print(df.head(3))

# Check specifically for numeric conversion failure
cols_to_check = ["cpu_time_ms", "peak_rss_mb", "energy_joules", "duration_ms"]
print("\n--- Checking Critical Numeric Columns ---")
for col in cols_to_check:
    if col in df.columns:
        numeric_vals = pd.to_numeric(df[col], errors='coerce')
        failures = numeric_vals.isna().sum()
        print(f"Column '{col}': {failures} rows are not valid numbers")
    else:
        print(f"Column '{col}': MISSING entirely")
