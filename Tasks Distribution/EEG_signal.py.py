import numpy as np
import matplotlib.pyplot as plt

# ================= CONFIG ================= #
FILE_1 = "F001.txt"
FILE_2 = "N032.TXT"

# ================= LOAD EEG SIGNALS ================= #
eeg_1 = np.loadtxt(FILE_1)
eeg_2 = np.loadtxt(FILE_2)

# Make both signals same length for clean overlap
min_len = min(len(eeg_1), len(eeg_2))
eeg_1 = eeg_1[:min_len]
eeg_2 = eeg_2[:min_len]

# ================= DATA POINT AXIS ================= #
x = np.arange(min_len)   # data points (sample index)

# ================= PLOT (OVERLAPPING) ================= #
plt.figure(figsize=(10, 6))

plt.plot(x, eeg_1, label="Task1:F001.txt", color="tab:blue", linewidth=0.8)
plt.plot(x, eeg_2, label="Task2:N032.txt", color="tab:red", linewidth=0.8, alpha=0.8)

# ---- Labels & Legend ----
plt.xlabel("EEG Data Samples", fontsize=20)
plt.ylabel("Amplitude (µV)", fontsize=20)

plt.legend(fontsize=16)
plt.grid(True, linestyle="--", alpha=0.6)

# ---- Increase numeric (tick) font size ----
plt.tick_params(axis='both', labelsize=18)

# ---- Save as PDF ----
plt.savefig("eeg_overlay_datapoints.pdf", format="pdf", bbox_inches="tight")

plt.tight_layout()
plt.show()
