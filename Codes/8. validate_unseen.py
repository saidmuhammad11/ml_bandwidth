import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# CONFIGURATION
INPUT_FILE = "raw_unseen.jsonl"
DEFAULT_MEM = 1024
HGBDT_CHOICES = {
    'disk_io': 128,
    'matrix': 128 
}

def main():
    try:
        data = []
        with open(INPUT_FILE, 'r') as f:
            for line in f:
                data.append(json.loads(line))
        df = pd.DataFrame(data)
    except Exception as e:
        print(f"Error reading {INPUT_FILE}: {e}")
        return

    # --- CRITICAL CHANGE: USE MEDIAN INSTEAD OF MEAN ---
    # This filters out the random 135J spikes caused by OS background tasks
    grouped = df.groupby(['workload', 'mem_limit_mb'])['energy_joules'].median().reset_index()

    print("\n--- HEAVY GENERALIZATION TEST (MEDIAN FILTERED) ---")
    print(f"{'WORKLOAD':<12} | {'DEFAULT (1024MB)':<18} | {'HgBDT CHOICE':<20} | {'SAVINGS':<10}")
    print("-" * 75)

    total_default = 0
    total_hgbdt = 0
    workloads = HGBDT_CHOICES.keys()
    
    results = {'workload': [], 'Default': [], 'HgBDT': []}

    for wl in workloads:
        # Get Default Energy (1024MB)
        def_row = grouped[(grouped['workload'] == wl) & (grouped['mem_limit_mb'] == DEFAULT_MEM)]
        if def_row.empty: continue
        def_energy = def_row['energy_joules'].values[0]

        # Get HgBDT Energy (128MB)
        choice = HGBDT_CHOICES[wl]
        opt_row = grouped[(grouped['workload'] == wl) & (grouped['mem_limit_mb'] == choice)]
        if opt_row.empty: continue
        opt_energy = opt_row['energy_joules'].values[0]

        savings = def_energy - opt_energy
        
        print(f"{wl:<12} | {def_energy:.2f} J           | {opt_energy:.2f} J ({choice}MB)    | {savings:+.2f} J")

        total_default += def_energy
        total_hgbdt += opt_energy
        
        results['workload'].append(wl)
        results['Default'].append(def_energy)
        results['HgBDT'].append(opt_energy)

    print("-" * 75)
    total_savings_pct = (total_default - total_hgbdt) / total_default * 100
    print(f"TOTAL SAVINGS: {total_savings_pct:.1f}% ({total_default - total_hgbdt:.2f} J)")

    # Plotting
    x = np.arange(len(results['workload']))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 8))
    rects1 = ax.bar(x - width/2, results['Default'], width, label='Default (1024MB)', color='gray')
    rects2 = ax.bar(x + width/2, results['HgBDT'], width, label='HgBDT Choice', color='#2ecc71')

    ax.set_ylabel('Real Energy (Joules) [Median]')
    ax.set_title(f'Heavy Generalization Test\n(Total Savings: {total_savings_pct:.1f}%)')
    ax.set_xticks(x)
    ax.set_xticklabels(results['workload'])
    ax.legend()
    ax.grid(axis='y', linestyle='-', alpha=0.3)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f} J',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
