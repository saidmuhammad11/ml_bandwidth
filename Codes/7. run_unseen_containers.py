import subprocess
import json
import time
import os
import sys

# Path to workloads
HOST_WORKLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../serverless-exp/workloads"))
IMAGE_NAME = "serverless-runner:ubuntu22" 
OUTPUT_FILE = "raw_unseen.jsonl"
RAPL_FILE = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"
MEMORY_SIZES = [128, 256, 512, 1024]
NEW_WORKLOADS = ['disk_io', 'matrix']
ITERATIONS = 5

def read_energy():
    try:
        with open(RAPL_FILE, 'r') as f:
            return int(f.read())
    except: return 0

def run_container(workload, mem_mb):
    event_json = json.dumps({"workload": workload})
    
    cmd = [
        "docker", "run", "--rm",
        "--entrypoint", "",
        f"--memory={mem_mb}m",
        "--cpus=1.0",
        "-v", f"{HOST_WORKLOAD_DIR}:/app",
        "-w", "/app",
        IMAGE_NAME,
        "python3", "workload.py",
        f"{event_json}"
    ]
    
    start_time = time.time()
    start_energy = read_energy()
    
    try:
        # Capture BOTH stdout and stderr
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # DEBUG: Print output if it was too fast (< 2 seconds)
        duration = time.time() - start_time
        if duration < 2.0:
            print(f"  [WARNING] Too fast ({duration:.2f}s)! Output:")
            print(f"  STDOUT: {result.stdout}")
            print(f"  STDERR: {result.stderr}")

    except Exception as e:
        print(f"  [Error] {e}")
        return None
        
    end_energy = read_energy()
    end_time = time.time()
    
    duration_ms = (end_time - start_time) * 1000
    energy_joules = (end_energy - start_energy) / 1_000_000
    
    return {
        "workload": workload,
        "mem_limit_mb": mem_mb,
        "duration_ms": duration_ms,
        "cpu_time_ms": duration_ms, 
        "energy_joules": energy_joules,
        "io_read_bytes": 0,
        "io_write_bytes": 0
    }

def main():
    print(f"--- COLLECTING HEAVY DATA (5s Duration) ---")
    if not os.path.exists(HOST_WORKLOAD_DIR):
        print(f"Error: {HOST_WORKLOAD_DIR} not found.")
        return

    results = []
    
    for wl in NEW_WORKLOADS:
        for mem in MEMORY_SIZES:
            print(f"\nBenchmarking {wl} @ {mem}MB ...")
            for i in range(ITERATIONS):
                data = run_container(wl, mem)
                if data:
                    print(f"  Run {i+1}: {data['energy_joules']:.2f} J | {data['duration_ms']:.0f} ms")
                    results.append(data)
                time.sleep(1) 
                
    with open(OUTPUT_FILE, "w") as f:
        for row in results:
            f.write(json.dumps(row) + "\n")
    print(f"\n[DONE] Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()