import os
import sys
import random
import numpy as np
import json
import matplotlib.pyplot as plt

# ================= CONFIG ================= #
TASK_POINTS = [100, 200, 300, 400, 500]
NODE_COUNTS = [3, 6, 9]
ITERATIONS = 200

Y_CYCLES_PER_BIT = 1000
ETA_DELAY_COST = 1e-3      # properly scaled
KAPPA_PRICE_GAIN = 1e-12   # scaled for cycles
P_BASE_DEFAULT = 1e-12

np.random.seed(42)
random.seed(42)

# ================= FOG NODES ================= #
FOG_NODES = [
    {"name": "F1", "MIPS": 12000},
    {"name": "F2", "MIPS": 16000},
    {"name": "F3", "MIPS": 17000},
    {"name": "F4", "MIPS": 14000},  # Fog Head (Leader)
    {"name": "F5", "MIPS": 18000},
    {"name": "F6", "MIPS": 10000},
    {"name": "F7", "MIPS": 15000},
    {"name": "F8", "MIPS": 19000},
    {"name": "F9", "MIPS": 20000},
    {"name": "F10", "MIPS": 21000}
]

FOG_HEAD_NAME = "F4"

# ================= DELAY ================= #
def processing_delay(task_cycles, mips):
    return task_cycles / (mips * 1e6)

# ================= TRUE STACKELBERG ================= #
def simulate_stackelberg_processing_delay(task_sizes, num_nodes):

    # Fixed provider set (no randomness bias)
    providers = [n for n in FOG_NODES if n["name"] != FOG_HEAD_NAME]
    providers = sorted(providers, key=lambda x: -x["MIPS"])
    selected_nodes = providers[:num_nodes]

    # Queue completion time per node
    completion_time = {n["name"]: 0.0 for n in selected_nodes}

    for size_bytes in task_sizes:

        task_cycles = size_bytes * 8 * Y_CYCLES_PER_BIT

        # ---------- LEADER: Fog Head pricing ----------
        prices = {}
        for n in selected_nodes:
            mu = n["MIPS"] * 1e6
            prices[n["name"]] = (
                P_BASE_DEFAULT +
                KAPPA_PRICE_GAIN * (completion_time[n["name"]] / mu)
            )

        # ---------- FOLLOWERS: task best response ----------
        best_cost = float("inf")
        best_node = None
        best_proc_delay = None

        for n in selected_nodes:
            proc_delay = processing_delay(task_cycles, n["MIPS"])
            expected_finish = completion_time[n["name"]] + proc_delay

            cost = (
                prices[n["name"]] * task_cycles +
                ETA_DELAY_COST * expected_finish
            )

            if cost < best_cost:
                best_cost = cost
                best_node = n
                best_proc_delay = proc_delay

        completion_time[best_node["name"]] += best_proc_delay

    # SYSTEM DELAY = makespan
    return max(completion_time.values())

# ================= MAIN ================= #
if len(sys.argv) < 2:
    print("Usage: python stackelberg_true.py dataset_path")
    sys.exit(1)

dataset_path = sys.argv[1]

files = sorted([
    os.path.join(dataset_path, f)
    for f in os.listdir(dataset_path)
    if os.path.isfile(os.path.join(dataset_path, f))
])

if len(files) < 500:
    raise ValueError("Dataset must contain at least 500 files")

task_sizes_all = [os.path.getsize(f) for f in files[:500]]

results = {n: [] for n in NODE_COUNTS}

for task_count in TASK_POINTS:
    print(f"Processing {task_count} tasks...")
    task_subset = task_sizes_all[:task_count]

    for n_nodes in NODE_COUNTS:
        delays = []
        for _ in range(ITERATIONS):
            delays.append(
                simulate_stackelberg_processing_delay(task_subset, n_nodes)
            )
        results[n_nodes].append(np.mean(delays))

# ================= SAVE RESULTS ================= #
json_results = {}
for i, t in enumerate(TASK_POINTS):
    json_results[str(t)] = {}
    for n in NODE_COUNTS:
        json_results[str(t)][f"{n}_nodes"] = results[n][i]

with open("stackelberg_true_proc_delay.json", "w") as f:
    json.dump(json_results, f, indent=4)

# ================= PLOT ================= #
def autolabel(bars):
    for bar in bars:
        h = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2,
            h,
            f"{h:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
            rotation=90
        )

x = np.arange(len(TASK_POINTS))
bar_width = 0.22

plt.figure(figsize=(12, 7))

for i, n in enumerate(NODE_COUNTS):
    bars = plt.bar(
        x + i*bar_width,
        results[n],
        bar_width,
        label=f"{n} Fog Nodes"
    )
    autolabel(bars)

plt.xlabel("Number of Tasks")
plt.ylabel("System Processing Delay (seconds)")
plt.title(
    "System Processing Delay vs Number of Tasks\n"
    "True Stackelberg Offloading (Fog Head = F4)"
)
plt.xticks(x + bar_width, TASK_POINTS)
plt.legend()
plt.grid(axis="y")
plt.tight_layout()
plt.show()
