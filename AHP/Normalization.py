import json
from openpyxl import Workbook

# Load sorted scores from file
with open("sorted_scores.json", "r") as f:
    sorted_scores = json.load(f)

# Define the node data (only names are needed for lookup)
nodes = [
    {"name": "F1"},
    {"name": "F2"},
    {"name": "F3"},
    {"name": "F4"},
    {"name": "F5"},
    {"name": "F6"},
    {"name": "F7"},
    {"name": "F8"},
    {"name": "F9"},
    {"name": "F10"}
]

# Create lookup dictionaries for scores
processor_scores = {node["name"]: node["Processor Score"] for node in sorted_scores["Processor"]}
energy_scores = {node["name"]: node["Energy Score"] for node in sorted_scores["Energy"]}
memory_scores = {node["name"]: node["Memory Score"] for node in sorted_scores["Memory"]}

# Find min and max for normalization
min_processor = min(processor_scores.values())
max_processor = max(processor_scores.values())

min_memory = min(memory_scores.values())
max_memory = max(memory_scores.values())

min_energy = min(energy_scores.values())
max_energy = max(energy_scores.values())

print("Normalized Node Scores:\n")

# Normalize and attach values to each node
for node in nodes:
    name = node["name"]
    
    processor = processor_scores[name]
    memory = memory_scores[name]
    energy = energy_scores[name]
    
    # Normalize Processor (min-max)
    processor_norm = (processor - min_processor) / (max_processor - min_processor)

    # Normalize Memory (min-max)
    memory_norm = (memory - min_memory) / (max_memory - min_memory)
    
    # Normalize Energy (reverse min-max)
    energy_norm = (max_energy - energy) / (max_energy - min_energy)
    
    node["Processor Norm"] = round(processor_norm, 6)
    node["Memory Norm"] = round(memory_norm, 6)
    node["Energy Norm"] = round(energy_norm, 6)
    
    print(f"Node: {name}")
    print(f" Processor Norm: {processor_norm:.6f}")
    print(f" Memory Norm: {memory_norm:.6f}\n")
    print(f" Energy Norm: {energy_norm:.6f}")

# Save normalized data to a JSON file
with open("normalized.json", "w") as f:
    json.dump(nodes, f, indent=4)

print("Normalized values saved to 'normalized.json'")

# Create an Excel file using openpyxl
wb = Workbook()
ws = wb.active
ws.title = "Normalized Scores"

# Write headers
headers = ["Node", "Processor Norm", "Memory Norm", "Energy Norm"]
ws.append(headers)

# Write data rows
for node in nodes:
    row = [
        node["name"],
        node["Processor Norm"],
        node["Memory Norm"],
        node["Energy Norm"]
    ]
    ws.append(row)

# Save the Excel file
wb.save("normalized.xlsx")
print("Normalized values saved to 'normalized.xlsx'")
