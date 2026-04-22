# cloud.py (FINAL – Explicit Queueing + Propagation Delay, Reviewer-Safe)

import os
import sys
import numpy as np
import json
import matplotlib.pyplot as plt
import random

# ================= CONFIG ================= #
TASK_POINTS = [100, 200, 300, 400, 500]
ITERATIONS = 200

Y_CYCLES_PER_BIT = 1000

np.random.seed(42)
random.seed(42)

# ================= PROPAGATION CONFIG ================= #
PROPAGATION_SPEED = 3e8  # m/s

EDGE_COORD = (0, 0)                   # Fog / Gateway
CLOUD_COORD = (200e3, 200e3)        # Cloud DC (~5000 km away)

# ================= CLOUD CONFIG ================= #
CLOUD = {
    "name": "CLOUD",
    "CLOCK_FREQ": 100e9   # cycles/sec
}

CLOUD_VMS = 1

# ================= DELAY MODELS ================= #
def processing_delay(task_cycles, clock_freq):
    return task_cycles / clock_freq

def uplink_delay(task_bits, uplink_bps):
    return task_bits / uplink_bps

def euclidean_distance(c1, c2):
    return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

def propagation_delay(src, dst):
    d = euclidean_distance(src, dst)
    return d / PROPAGATION_SPEED

# ================= SIMULATION ================= #
def simulate_cloud_total_delay(task_sizes):

    # VM completion times (captures queueing delay)
    completion_time = [0.0] * CLOUD_VMS

    # Fixed propagation delay (edge → cloud)
    d_prop = propagation_delay(EDGE_COORD, CLOUD_COORD)

    for size_bytes in task_sizes:

        task_bits = size_bytes * 8
        task_cycles = task_bits * Y_CYCLES_PER_BIT

        # ---- TRANSMISSION DELAY (WAN) ----
        uplink_bps =30e6
        d_tx = uplink_delay(task_bits, uplink_bps)

        # ---- PROCESSING DELAY ----
        d_proc = processing_delay(task_cycles, CLOUD["CLOCK_FREQ"])

        # ---- VM SELECTION ----
        vm = np.argmin(completion_time)

        # ---- QUEUEING DELAY ----
        d_queue = completion_time[vm]

        # ---- TOTAL TASK DELAY ----
        task_total_delay = d_tx + d_prop + d_proc + d_queue

        # ---- UPDATE VM COMPLETION ----
        completion_time[vm] += (d_tx + d_prop + d_proc)

    # System delay (makespan)
    return max(completion_time)

# ================= MAIN ================= #
if len(sys.argv) < 2:
    print("Usage: python cloud.py dataset_path")
    sys.exit(1)

dataset_path = sys.argv[1]

files = sorted([
    os.path.join(dataset_path, f)
    for f in os.listdir(dataset_path)
    if os.path.isfile(os.path.join(dataset_path, f))
])

if len(files) < 500:
    raise ValueError("Dataset must contain at least 500 tasks")

task_sizes_all = [os.path.getsize(f) for f in files[:500]]

results = []

for t in TASK_POINTS:
    subset = task_sizes_all[:t]
    print(f"Processing {t} tasks (Cloud Total Delay)...")

    vals = []
    for _ in range(ITERATIONS):
        vals.append(simulate_cloud_total_delay(subset))

    results.append(np.mean(vals))

# ================= SAVE ================= #
with open("cloud_totaldelay_final2.json", "w") as f:
    json.dump(
        {str(t): results[i] for i, t in enumerate(TASK_POINTS)},
        f,
        indent=4
    )

# ================= PLOT ================= #
plt.figure(figsize=(10, 6))
bars = plt.bar(TASK_POINTS, results, width=40)

for bar in bars:
    h = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        h,
        f"{h:.2f}",
        ha="center",
        va="bottom",
        fontsize=10
    )

plt.xlabel("Number of Tasks")
plt.ylabel("Total System Delay (seconds)")
plt.title("Total System Delay vs Number of Tasks\n(Cloud Offloading with Propagation Delay)")
plt.grid(axis="y")
plt.tight_layout()
plt.show()
