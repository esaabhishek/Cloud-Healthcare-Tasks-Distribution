import numpy as np
import json
import pandas as pd

# Step 1: Load normalized data
with open("normalized.json", "r") as f:
    nodes = json.load(f)

# Step 2: Define the input matrix
matrix = np.array([
    [1, 0.8543, 0.6388],
    [1.1705, 1, 0.7478],
    [1.5652, 1.3372, 1]
], dtype=float)

# Step 3: Normalize the matrix column-wise
col_sums = np.sum(matrix, axis=0)
normalized_matrix = matrix / col_sums

# Step 4: Calculate row averages to get weights
weights = np.mean(normalized_matrix, axis=1)
weight_proc = weights[0]
weight_mem = weights[1]
weight_ene = weights[2]

print("Weights:")
print(f" Processor Weight: {weight_proc:.6f}")
print(f" Memory Weight: {weight_mem:.6f}")
print(f" Energy Weight: {weight_ene:.6f}")

# Step 5: Calculate AHP score for each node
ahp_scores = []
for idx, node in enumerate(nodes, 1):
    name = node["name"]
    processor = node["Processor Norm"]
    memory = node["Memory Norm"]
    energy = node["Energy Norm"]

    AHP_Score = (weight_proc * processor) + (weight_mem * memory) + (weight_ene * energy)

    ahp_scores.append({
        "Node Name": name,
        "Processor Norm": round(processor, 6),
        "Memory Norm": round(memory, 6),
        "Energy Norm": round(energy, 6),
        "AHP Score": round(AHP_Score, 6)
    })

# Step 6: Save the result to a JSON file
with open("DD_ahp_results.json", "w") as f:
    json.dump(ahp_scores, f, indent=4)

# Step 7: Create a DataFrame and save to an Excel file
df = pd.DataFrame(ahp_scores)
df.to_excel("DD_ahp_results.xlsx", index=False)

print("AHP scores saved to 'ahp_scores_from_custom_matrix.json' and 'ahp_scores.xlsx'")
