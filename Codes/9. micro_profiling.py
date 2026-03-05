import subprocess
import json
import time
import os
import csv
import sys

# CONFIGURATION
HOST_WORKLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../serverless-exp/workloads"))
IMAGE_NAME = "serverless-runner:ubuntu22"
OUTPUT_CSV = "micro_metrics.csv"
MEMORY_SIZES = [128, 256, 512, 1024]
# We only profile the heavy ones for the paper insights
WORKLOADS = ['disk_io', 'matrix', 'memory_touch'] 
ITERATIONS = 3

# We map raw perf names to our Clean CSV headers
EVENT_MAPPING = {
    "instructions": "instructions",
    "cpu_core/instructions/": "instructions",
    "cpu_atom/instructions/": "instructions",
    
    "cycles": "cycles",
    "cpu_core/cycles/": "cycles",
    "cpu_atom/cycles/": "cycles",
    
    "LLC-misses": "LLC-misses",
    "cpu_core/LLC-misses/": "LLC-misses",
    "cpu_atom/LLC-misses/": "LLC-misses",
    
    "L1-dcache-misses": "L1-dcache-misses",
    "cpu_core/L1-dcache-misses/": "L1-dcache-misses",
    "cpu_atom/L1-dcache-misses/": "L1-dcache-misses",
    
    "page-faults": "page-faults",
    "context-switches": "context-switches"
}

PERF_EVENTS = [
    "instructions", 
    "cycles", 
    "LLC-misses", 
    "L1-dcache-misses", 
    "page-faults", 
    "context-switches"
]

def run_perf_container(workload, mem_mb):
    print(f"   Profiling {workload} @ {mem_mb}MB...", end=" ", flush=True)
    
    event_json = json.dumps({"workload": workload})
    
    # Start Docker in Background
    docker_start_cmd = [
        "docker", "run", "-d", "--rm",
        "--entrypoint", "",
        "-e", "PROFILE_MODE=1",  # <--- NEW LINE: Trigger the sleep only here
        f"--memory={mem_mb}m",
        "--cpus=1.0",
        "-v", f"{HOST_WORKLOAD_DIR}:/app",
        "-w", "/app",
        IMAGE_NAME,
        "python3", "workload.py",
        f"{event_json}"
    ]
    
    container_id = None
    try:
        # 1. Start Container
        container_id = subprocess.check_output(docker_start_cmd, text=True).strip()
        
        # 2. Get PID
        inspect_cmd = ["docker", "inspect", "--format", "{{.State.Pid}}", container_id]
        container_pid = subprocess.check_output(inspect_cmd, text=True).strip()
        
        if not container_pid:
            print("[Error: No PID]")
            return None

        # 3. Attach perf to PID
        perf_cmd = ["sudo", "perf", "stat", "-x,", "-e", ",".join(PERF_EVENTS), "-p", container_pid]
        
        result = subprocess.run(perf_cmd, capture_output=True, text=True)
        
        # 4. Hybrid CPU Parser
        # We sum up values if they are split between cpu_core and cpu_atom
        metrics = {k: 0.0 for k in set(EVENT_MAPPING.values())}
        
        for line in result.stderr.splitlines():
            parts = line.split(',')
            if len(parts) >= 3:
                try:
                    val_str = parts[0]
                    name_raw = parts[2]
                    
                    # Skip "<not counted>" or empty values
                    if val_str == "<not counted>" or val_str == "<not supported>" or not val_str:
                        continue
                        
                    val = float(val_str)
                    
                    # Check if this raw name maps to one of our target metrics
                    if name_raw in EVENT_MAPPING:
                        clean_name = EVENT_MAPPING[name_raw]
                        metrics[clean_name] += val
                except: continue
        
        metrics['workload'] = workload
        metrics['mem_limit'] = mem_mb
        
        # Debug Output
        instr = metrics.get('instructions', 0)
        cyc = metrics.get('cycles', 1)
        ipc = instr / cyc if cyc > 0 else 0
        misses = metrics.get('LLC-misses', 0)
        
        print(f"-> IPC: {ipc:.2f} | LLC Misses: {misses:.0f} | Faults: {metrics.get('page-faults',0):.0f}")
        
        return metrics

    except Exception as e:
        print(f"\n[Exception] {e}")
        if container_id:
            try: subprocess.run(["docker", "kill", container_id], capture_output=True)
            except: pass
        return None

def main():
    print("--- STARTING MICRO-ARCHITECTURAL PROFILING (HYBRID CPU FIX) ---")
    
    # Headers for CSV (Target Clean Names)
    clean_headers = ['workload', 'mem_limit'] + list(set(EVENT_MAPPING.values()))
    
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=clean_headers)
        writer.writeheader()
        
        for wl in WORKLOADS:
            for mem in MEMORY_SIZES:
                for i in range(ITERATIONS):
                    data = run_perf_container(wl, mem)
                    if data:
                        # Filter data to match headers
                        row = {k: data.get(k, 0) for k in clean_headers}
                        writer.writerow(row)
                        f.flush()
                    
    print(f"\n[DONE] Saved micro-metrics to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()