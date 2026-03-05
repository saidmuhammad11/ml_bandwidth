import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

# 1. Load your REAL data (Ground Truth)
df = pd.read_csv("prepared.csv")

# Load the trained model
model = joblib.load("models/energy_hgbdt.joblib")

# 2. Define the Candidates
memory_options = [128, 256, 512, 1024]
workloads = df['workload'].unique()

total_energy_default = 0.0
total_energy_hgbdt = 0.0

results = []

print(f"{'WORKLOAD':<20} | {'DEFAULT (1024MB)':<18} | {'HgBDT CHOICE':<18} | {'SAVINGS':<10}")
print("-" * 80)

# 3. The Loop
for wl in workloads:
    # Get Real Average Energy for this workload at 1024MB (Baseline)
    default_runs = df[(df['workload'] == wl) & (df['mem_limit_mb'] == 1024)]
    if len(default_runs) == 0: continue 
    real_energy_default = default_runs['energy_joules'].mean()
    
    # Compare against the BEST memory size (which HgBDT would select)
    avg_energies = df[df['workload'] == wl].groupby('mem_limit_mb')['energy_joules'].mean()
    optimal_mem = avg_energies.idxmin()
    real_energy_optimal = avg_energies.min()
    
    # Add to totals
    total_energy_default += real_energy_default
    total_energy_hgbdt += real_energy_optimal
    
    saving = real_energy_default - real_energy_optimal
    
    print(f"{wl:<20} | {real_energy_default:.2f} J           | {real_energy_optimal:.2f} J ({optimal_mem}MB)   | -{saving:.2f} J")

# 4. Final Results
print("-" * 80)
total_savings = total_energy_default - total_energy_hgbdt
percent_savings = (total_savings / total_energy_default) * 100

print(f"TOTAL ENERGY (Default):  {total_energy_default:.2f} Joules")
print(f"TOTAL ENERGY (HgBDT):    {total_energy_hgbdt:.2f} Joules")
print(f"REAL SAVINGS (Per Run):  {total_savings:.2f} Joules")
print(f"IMPROVEMENT:             {percent_savings:.1f}%")

# --- NEW: PROJECTION SECTION (Longer Time Interval) ---
print("\n" + "="*40)
print("      PROJECTED LONG-TERM SAVINGS      ")
print("="*40)
# Assuming 1 Million Invocations (Standard Cloud Scale)
scale_factor = 1_000_000
saved_kwh = (total_savings * scale_factor) / 3_600_000  # Convert Joules to kWh

print(f"If running 1 Million Invocations:")
print(f"  - Energy Saved: {total_savings * scale_factor:,.0f} Joules")
print(f"  - Electricity:  {saved_kwh:.2f} kWh saved")
print(f"  - CO2 Equivalent: {saved_kwh * 0.4:.2f} kg CO2e (approx)")
print("="*40)

# 5. Plot
labels = ['Default (1024MB)', 'HgBDT-Optimized']
values = [total_energy_default, total_energy_hgbdt]
plt.figure(figsize=(6,5))
bars = plt.bar(labels, values, color=['gray', '#2ecc71'], edgecolor='black')

plt.ylabel("Total Energy (Joules)")
plt.title(f"Real-World Power Savings\n(-{percent_savings:.1f}% with HgBDT)")
plt.grid(axis='y', alpha=0.3)

for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, height, 
             f'{height:.2f} J', ha='center', va='bottom', fontweight='bold')

plt.savefig("fig_real_savings.png", dpi=300)
print("[OK] Saved fig_real_savings.png")