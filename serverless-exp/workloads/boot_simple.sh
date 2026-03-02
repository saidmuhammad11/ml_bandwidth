#!/bin/bash
workloads=("cpuintensive" "memory_touch" "mixed_touch_cpu")
mems=(128 256 512 1024)

for w in "${workloads[@]}"; do
  for m in "${mems[@]}"; do
    echo "Starting experiment: $w with $m MB"
    python3 workloads/harness_linux.py \
        --workload "$w" \
        --mem_limit_mb "$m" \
        --runs 100 \
        --cold_every 5 \
        --log "/app/workloads/raw.jsonl"
  done
done
