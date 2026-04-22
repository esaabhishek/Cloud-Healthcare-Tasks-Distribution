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
ETA_DELAY_COST = 1e-3

PRICE_GRID = np.linspace(1e-12, 5e-12, 8)

np.random.seed(42)
random.seed(42)

# ================= PROPAGATION CONFIG ================= #
PROPAGATION_SPEED = 3e8  # m/s

NODE_COORDS = {
    "F1":  (110, 120),
    "F2":  (130, 150),
    "F3":  (150, 130),
    "F4":  (170, 110),   # Fog Head
    "F5":  (190, 140),
    "F6":  (120, 180),
    "F7":  (140, 190),
    "F8":  (160, 170),
    "F9":  (180, 160),
    "F10": (195, 185)
}

# ================= FOG NODES ================= #
FOG_NODES = [
    {"name": "F1", "CLOCK_FREQ": 50e9, "uplink": 30e6},
    {"name": "F2", "CLOCK_FREQ": 50e9, "uplink": 30e6},
    {"name": "F3", "CLOCK_FREQ": 50e9, "uplink": 30e6},
    {"name": "F4", "CLOCK_FREQ": 50e9, "uplink": 30e6},  # Fog Head
    {"name": "F5", "CLOCK_FREQ": 50e9, "uplink": 30e6},
    {"name": "F6", "CLOCK_FREQ": 50e9, "uplink":30e6},
    {"name": "F7", "CLOCK_FREQ": 50e9, "uplink": 30e6},
    {"name": "F8", "CLOCK_FREQ": 50e9, "uplink": 30e6},
    {"name": "F9", "CLOCK_FREQ": 50e9, "uplink": 30e6},
    {"name": "F10","CLOCK_FREQ": 50e9, "uplink": 30e6}
]

FOG_HEAD_NAME = "F4"

# ================= DELAY MODELS ================= #
def processing_delay(task_cycles, clock_freq):
    return task_cycles / clock_freq

def uplink_delay(task_bits, uplink_bps):
    return task_bits / uplink_bps

def euclidean_distance(c1, c2):
    return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

def propagation_delay(src, dst):
    d = euclidean_distance(NODE_COORDS[src], NODE_COORDS[dst])
    return d / PROPAGATION_SPEED

# ================= TRUE STACKELBERG ================= #
def simulate_true_stackelberg_total_delay(task_sizes, num_nodes):

    providers = [n for n in FOG_NODES if n["name"] != FOG_HEAD_NAME]
    selected_nodes = providers[:num_nodes]

    # implicit queueing delay
    completion_time = {n["name"]: 0.0 for n in selected_nodes}

    for size_bytes in task_sizes:

        task_bits = size_bytes * 8
        task_cycles = task_bits * Y_CYCLES_PER_BIT

        best_leader_revenue = -1
        best_assignment = None
        best_task_delay = None

        for price in PRICE_GRID:

            best_cost = float("inf")
            chosen_node = None
            chosen_delay = None

            for n in selected_nodes:
                d_up = uplink_delay(task_bits, n["uplink"])
                d_proc = processing_delay(task_cycles, n["CLOCK_FREQ"])
                d_prop = propagation_delay(FOG_HEAD_NAME, n["name"])

                service_delay = d_up + d_prop + d_proc
                expected_finish = completion_time[n["name"]] + service_delay

                cost = price * task_cycles + ETA_DELAY_COST * expected_finish

                if cost < best_cost:
                    best_cost = cost
                    chosen_node = n
                    chosen_delay = service_delay

            leader_revenue = price * task_cycles

            if leader_revenue > best_leader_revenue:
                best_leader_revenue = leader_revenue
                best_assignment = chosen_node
                best_task_delay = chosen_delay

        completion_time[best_assignment["name"]] += best_task_delay

    return max(completion_time.values())

# ================= MAIN ================= #
if len(sys.argv) < 2:
    print("Usage: python wei_avg_node.py dataset_path")
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

# ================= RUN EXPERIMENT ================= #
results = {n: [] for n in NODE_COUNTS}

for t in TASK_POINTS:
    subset = task_sizes_all[:t]
    print(f"Processing {t} tasks...")

    for n_nodes in NODE_COUNTS:
        delays = []
        for _ in range(ITERATIONS):
            delays.append(
                simulate_true_stackelberg_total_delay(subset, n_nodes)
            )
        results[n_nodes].append(np.mean(delays))

# ================= WEIGHTED AVERAGE ================= #
weights = {3: 3, 6: 6, 9: 9}
total_weight = sum(weights.values())

weighted_avg_delays = []

for i in range(len(TASK_POINTS)):
    weighted_sum = sum(
        weights[n] * results[n][i] for n in NODE_COUNTS
    )
    weighted_avg_delays.append(weighted_sum / total_weight)

# ================= SAVE ================= #
with open("weighted_avg_totaldelay.json", "w") as f:
    json.dump(
        {
            str(TASK_POINTS[i]): weighted_avg_delays[i]
            for i in range(len(TASK_POINTS))
        },
        f,
        indent=4
    )

# ================= PLOT ================= #
plt.figure(figsize=(10, 6))

bars = plt.bar(TASK_POINTS, weighted_avg_delays)

for b in bars:
    h = b.get_height()
    plt.text(
        b.get_x() + b.get_width() / 2,
        h,
        f"{h:.2f}",
        ha="center",
        va="bottom",
        fontsize=10
    )

plt.xlabel("Number of Tasks")
plt.ylabel("Weighted Average Total Delay (seconds)")
plt.title("Weighted Average Total System Delay\n(True Stackelberg with Propagation Delay)")
plt.grid(axis="y")
plt.tight_layout()
plt.show()
