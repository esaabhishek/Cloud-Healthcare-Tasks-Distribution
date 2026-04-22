import json
import numpy as np
import matplotlib.pyplot as plt

# ================= CONFIG ================= #
TASK_POINTS = [100, 200, 300, 400, 500]
NODE_COUNTS = [3, 6, 9]

JSON_FILE = "true_totaldelay_final.json"

# ================= LOAD JSON ================= #
with open(JSON_FILE, "r") as f:
    data = json.load(f)

# Convert JSON to plotting format
results = {n: [] for n in NODE_COUNTS}

for i, t in enumerate(TASK_POINTS):
    for n in NODE_COUNTS:
        results[n].append(data[str(t)][f"{n}_nodes"])

# ================= PLOT ================= #
x = np.arange(len(TASK_POINTS))
w = 0.22

colors = {
    3: "#f34c4c",   # light red
    6: "#50bbf4",   # light blue
    9: "#74c476"    # green
}

plt.figure(figsize=(10, 6))

for i, n in enumerate(NODE_COUNTS):
    plt.bar(
        x + i * w,
        results[n],
        w,
        label=f"{n} HPDs",
        color=colors[n]
    )

# ---- Axis labels ----
plt.xlabel("Number of Tasks", fontsize=25)
plt.ylabel("Total Network delay(s)", fontsize=25)

# ---- Tick font sizes ----
plt.xticks(x + w, TASK_POINTS, fontsize=25)
plt.yticks(fontsize=25)

# ---- Grid (dotted horizontal lines) ----
plt.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.7)

# ---- Legend (left side, larger font) ----
plt.legend(
    loc="upper left",
    fontsize=25,
    frameon=True
)
plt.savefig("Totaldelay.pdf", format="pdf", bbox_inches="tight")
plt.tight_layout()
plt.show()
