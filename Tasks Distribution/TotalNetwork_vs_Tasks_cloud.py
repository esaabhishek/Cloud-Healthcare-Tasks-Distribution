# ================= CLOUD vs WEIGHTED FOG COMPARISON ================= #

import json
import numpy as np
import matplotlib.pyplot as plt

# ---------------- LOAD RESULTS ---------------- #
with open("cloud_totaldelay_final2.json", "r") as f:
    cloud_data = json.load(f)

with open("weighted_avg_totaldelay.json", "r") as f:
    fog_data = json.load(f)

TASK_POINTS = [100, 200, 300, 400, 500]

# ---------------- EXTRACT VALUES ---------------- #
cloud_vals = [cloud_data[str(t)] for t in TASK_POINTS]
fog_vals   = [fog_data[str(t)] for t in TASK_POINTS]

# ---------------- PLOTTING ---------------- #
x = np.arange(len(TASK_POINTS)) * 0.6   # very close task groups
w = 0.22                                  # slimmer bars

plt.figure(figsize=(10, 6))                # square figure

plt.bar(
    x - w/2,
    fog_vals,
    w,
    color="#f34c4c",
    label="Proposed work using HPDs"
)

plt.bar(
    x + w/2,
    cloud_vals,
    w,
    color="#50bbf4",
    label="Conventional Cloud analysis"
)

# ---- Axis labels ----
plt.xlabel("Number of Tasks", fontsize=18)
plt.ylabel("Total Network delay(s)", fontsize=18)

# ---- Tick font sizes ----
plt.xticks(x, TASK_POINTS, fontsize=20)
plt.yticks(fontsize=20)

# ---- Grid (dotted horizontal lines) ----
plt.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.7)

# ---- Legend ----
plt.legend(
    loc="upper left",
    fontsize=20,
    frameon=True,
    handlelength=2.5,
    labelspacing=1.0,
    borderpad=1.2
)

plt.tight_layout()
plt.show()
