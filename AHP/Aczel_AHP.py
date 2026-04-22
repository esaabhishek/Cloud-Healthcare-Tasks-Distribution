import numpy as np
import json
import pandas as pd

# Load normalized data
with open("normalized.json", "r") as f:
    normalized_data = json.load(f)

# Define input matrices
Proc = np.array([
    [1, 4, 3],
    [1/4, 1, 1/2],
    [1/3, 2, 1]
], dtype=float)

Mem = np.array([
    [1, 1/2, 1/3],
    [2, 1, 1],
    [3, 1, 1]
], dtype=float)

Ene = np.array([
    [1, 2, 1/2],
    [1/2, 1, 1/3],
    [2, 3, 1]
], dtype=float)

# Calculate combined matrix following Processor -> Memory -> Energy
result = (Proc * Mem * Ene) ** (1/3)
print("=== Combined Matrix (Processor → Memory → Energy) ===")
print(result)

# Row-wise scoring
row_scores = []
for i in range(result.shape[0]):
    row = result[i]
    product = np.prod(row)
    row_score = product ** (1/3)
    row_scores.append(row_score)

print("\n=== Row Scores ===")
for i, score in enumerate(row_scores, start=1):
    print(f"Row {i} Score: {score}")

total_score = sum(row_scores)
print(f"\nTotal Score: {total_score}")

# Weights calculation
weight_proc = row_scores[0] / total_score
weight_mem = row_scores[1] / total_score
weight_ene = row_scores[2] / total_score

print("\n=== Weights Calculation ===")
print(f"Processor Weight: {weight_proc}")
print(f"Memory Weight: {weight_mem}")
print(f"Energy Weight: {weight_ene}")

# Calculate AHP score for each node using Processor → Memory → Energy pattern
ahp_scores = []
print("\n=== AHP Scores for Each Node ===")
for node in normalized_data:
    name = node["name"]
    processor = node["Processor Norm"]
    memory = node["Memory Norm"]
    energy = node["Energy Norm"]
    AHP_Score = (weight_proc * processor) + (weight_mem * memory) + (weight_ene * energy)
    score_entry = {
        "name": name,
        "AHP Score": round(AHP_Score, 6)
    }
    ahp_scores.append(score_entry)
    print(f"Node: {name}")
    print(f"  Processor Norm: {processor}")
    print(f"  Memory Norm: {memory}")
    print(f"  Energy Norm: {energy}")
    print(f"  AHP Score: {round(AHP_Score, 6)}\n")

# Save only AHP scores to JSON file
with open("ahp_scores.json", "w") as f:
    json.dump(ahp_scores, f, indent=4)

print("AHP scores saved to 'ahp_scores.json'")

# Save everything to Excel
with pd.ExcelWriter("ahp_results.xlsx") as writer:
    # Save matrices
    pd.DataFrame(Proc, index=["Row 1", "Row 2", "Row 3"], columns=["Col 1", "Col 2", "Col 3"]).to_excel(writer, sheet_name="Processor Matrix")
    pd.DataFrame(Mem, index=["Row 1", "Row 2", "Row 3"], columns=["Col 1", "Col 2", "Col 3"]).to_excel(writer, sheet_name="Memory Matrix")
    pd.DataFrame(Ene, index=["Row 1", "Row 2", "Row 3"], columns=["Col 1", "Col 2", "Col 3"]).to_excel(writer, sheet_name="Energy Matrix")
    pd.DataFrame(result, index=["Row 1", "Row 2", "Row 3"], columns=["Col 1", "Col 2", "Col 3"]).to_excel(writer, sheet_name="Combined Matrix")
    
    # Save final AHP scores with details
    df_ahp = pd.DataFrame([
        {
            "Name": node["name"],
            "Processor Norm": node["Processor Norm"],
            "Memory Norm": node["Memory Norm"],
            "Energy Norm": node["Energy Norm"],
            "AHP Score": round((weight_proc * node["Processor Norm"]) + 
                               (weight_mem * node["Memory Norm"]) + 
                               (weight_ene * node["Energy Norm"]), 6)
        }
        for node in normalized_data
    ])
    df_ahp.to_excel(writer, sheet_name="AHP Scores", index=False)

print("All results saved to 'ahp_results.xlsx'")
