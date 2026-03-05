import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("micro_metrics.csv")

# 1. Calculate Derived Metrics
df['IPC'] = df['instructions'] / df['cycles']
df['Cache_Miss_Rate_Per_KInstr'] = (df['LLC-misses'] / df['instructions']) * 1000

# Setup Plots
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
sns.set_style("whitegrid")

# --- PLOT 1: Architectural Inefficiency (IPC vs Memory) ---
# "Show how memory tier affects microarchitectural behavior"
# Hypothesis: Giving more RAM might NOT increase IPC for IO tasks (Inefficiency)
sns.barplot(data=df, x='workload', y='IPC', hue='mem_limit', ax=axes[0], palette="viridis")
axes[0].set_title("Insight 1: Instructions Per Cycle (IPC)\n(Diminishing Returns of Memory)")
axes[0].set_ylabel("IPC (Higher is Better)")

# --- PLOT 2: Memory System Stress (LLC Misses) ---
# "Show cache/memory bandwidth interactions"
# Hypothesis: Matrix/MemTouch should thrash cache at low memory
sns.barplot(data=df, x='workload', y='LLC-misses', hue='mem_limit', ax=axes[1], palette="magma")
axes[1].set_title("Insight 2: Last Level Cache (LLC) Pressure")
axes[1].set_ylabel("Total LLC Misses (Lower is Better)")

# --- PLOT 3: Page Faults (The Performance Killer) ---
# "Show architectural inefficiency in provisioning"
# Hypothesis: 128MB causes high page faults for memory_touch, killing energy efficiency
sns.barplot(data=df, x='workload', y='page-faults', hue='mem_limit', ax=axes[2], palette="Reds")
axes[2].set_title("Insight 3: Memory Thrashing (Page Faults)")
axes[2].set_ylabel("Page Faults")
axes[2].set_yscale("log") # Log scale because faults can be huge

plt.tight_layout()
plt.savefig("fig_micro_insights.png", dpi=300)
print("Saved fig_micro_insights.png")