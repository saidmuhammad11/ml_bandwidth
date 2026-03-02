#!/bin/bash

workloads=("cpuintensive" "memory_touch" "mixed_touch_cpu")
mems=(128 256 512 1024)

for w in "${workloads[@]}"; do
  for m in "${mems[@]}"; do
    # Run the Python script directly (No Docker command needed!)
    # We loop 5 times as per your original request
    for r in 1 2 3 4 5; do
        echo "Running: Workload=$w | Memory=$m | Run=$r"
        
        python3 harness_linux.py \
            --workload "$w" \
            --mem_limit_mb "$m" \
            --runs 25 \
            --cold_every 5
    done
  done
done