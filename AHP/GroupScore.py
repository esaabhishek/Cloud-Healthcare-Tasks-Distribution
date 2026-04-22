import json
import pandas as pd

# Define the node data
nodes = [
    {
        "name": "F1",
        "Cores": 6,
        "Min CPU Freq (GHz)": 1.4,
        "Max CPU Freq (GHz)": 2,
        "MIPS": 12000,
        "Unit Energy (Processing) (J)": 31,
        "Idle Energy (J)": 7750,
        "RAM (GB)": 10,
        "Secondary Mem (GB)": 128,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F2",
        "Cores": 8,
        "Min CPU Freq (GHz)": 1.8,
        "Max CPU Freq (GHz)": 2.9,
        "MIPS": 16000,
        "Unit Energy (Processing) (J)": 33,
        "Idle Energy (J)": 9000,
        "RAM (GB)": 6,
        "Secondary Mem (GB)": 128,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F3",
        "Cores": 8,
        "Min CPU Freq (GHz)": 1.9,
        "Max CPU Freq (GHz)": 3,
        "MIPS": 17000,
        "Unit Energy (Processing) (J)": 32,
        "Idle Energy (J)": 11500,
        "RAM (GB)": 4,
        "Secondary Mem (GB)": 128,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F4",
        "Cores": 8,
        "Min CPU Freq (GHz)": 3.2,
        "Max CPU Freq (GHz)": 4.4,
        "MIPS": 14000,
        "Unit Energy (Processing) (J)": 34,
        "Idle Energy (J)": 8500,
        "RAM (GB)": 6,
        "Secondary Mem (GB)": 128,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F5",
        "Cores": 6,
        "Min CPU Freq (GHz)": 2.1,
        "Max CPU Freq (GHz)": 4,
        "MIPS": 18000,
        "Unit Energy (Processing) (J)": 45,
        "Idle Energy (J)": 13000,
        "RAM (GB)": 6,
        "Secondary Mem (GB)": 512,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F6",
        "Cores": 4,
        "Min CPU Freq (GHz)": 1.1,
        "Max CPU Freq (GHz)": 3.3,
        "MIPS": 10000,
        "Unit Energy (Processing) (J)": 30,
        "Idle Energy (J)": 6500,
        "RAM (GB)": 6,
        "Secondary Mem (GB)": 64,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F7",
        "Cores": 4,
        "Min CPU Freq (GHz)": 1.8,
        "Max CPU Freq (GHz)": 3.5,
        "MIPS": 15000,
        "Unit Energy (Processing) (J)": 43,
        "Idle Energy (J)": 10000,
        "RAM (GB)": 8,
        "Secondary Mem (GB)": 512,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F8",
        "Cores": 4,
        "Min CPU Freq (GHz)": 3,
        "Max CPU Freq (GHz)": 4.8,
        "MIPS": 19000,
        "Unit Energy (Processing) (J)": 48,
        "Idle Energy (J)": 14500,
        "RAM (GB)": 14,
        "Secondary Mem (GB)": 512,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F9",
        "Cores": 8,
        "Min CPU Freq (GHz)": 1.6,
        "Max CPU Freq (GHz)": 3.2,
        "MIPS": 20000,
        "Unit Energy (Processing) (J)": 40,
        "Idle Energy (J)": 14000,
        "RAM (GB)": 6,
        "Secondary Mem (GB)": 512,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    },
    {
        "name": "F10",
        "Cores": 8,
        "Min CPU Freq (GHz)": 1.8,
        "Max CPU Freq (GHz)": 3.5,
        "MIPS": 21000,
        "Unit Energy (Processing) (J)": 39,
        "Idle Energy (J)": 14200,
        "RAM (GB)": 6,
        "Secondary Mem (GB)": 512,
        "Max RAM": 14,
        "Max Secondary Mem": 512
    }
]

# Find max RAM and Secondary memory values
max_ram = max(node['RAM (GB)'] for node in nodes)
max_secondary = max(node['Secondary Mem (GB)'] for node in nodes)

# Function to sort nodes and extract name and score
def get_sorted_scores(nodes, score_key, reverse=False):
    sorted_nodes = sorted(nodes, key=lambda x: x[score_key], reverse=reverse)
    return [{"name": node["name"], score_key: node[score_key]} for node in sorted_nodes]

print("Unsorted Node Scores:\n")

# Calculate scores for each node and print them
for node in nodes:
    name = node['name']
    clock_freq = (node['Min CPU Freq (GHz)'] + node['Max CPU Freq (GHz)']) / 2
    processor = (clock_freq * 1e9) / (node['MIPS'] * 1e6)
    
    energy_for_operation = 2 * (node['Unit Energy (Processing) (J)'] * (4.6 * 1e3 / 10))
    energy_for_computation = node['Unit Energy (Processing) (J)'] * (4.6 / clock_freq)
    energy_total = energy_for_operation + energy_for_computation + node['Idle Energy (J)']
    
    memory = (0.5 * (node['RAM (GB)'] / node['Max RAM'])) + (0.5 * (node['Secondary Mem (GB)'] / node['Max Secondary Mem']))
    
    node['Processor Score'] = processor
    node['Memory Score'] = memory
    node['Energy Score'] = energy_total
    
    print(f"Node: {name}")
    print(f"  Processor Score: {processor:.6f}")
    print(f"  Memory Score: {memory:.6f}")
    print(f"  Energy Score: {energy_total:.6f}\n")

# Get sorted lists
sorted_processor = get_sorted_scores(nodes, 'Processor Score')
sorted_memory = get_sorted_scores(nodes, 'Memory Score')
sorted_energy = get_sorted_scores(nodes, 'Energy Score')

# Create the final dictionary to store sorted scores
sorted_scores = {
    "Processor": sorted_processor,
    "Memory": sorted_memory,
    "Energy": sorted_energy
}

# Save sorted scores to a JSON file
with open("sorted_scores.json", "w") as f:
    json.dump(sorted_scores, f, indent=4)

print("Sorted scores have been saved to 'sorted_scores.json'")

# Create Excel file
with pd.ExcelWriter("node_Groupscores.xlsx") as writer:
    # Save unsorted node scores
    df_unsorted = pd.DataFrame(nodes)[['name', 'Processor Score', 'Memory Score', 'Energy Score']]
    df_unsorted.to_excel(writer, index=False, sheet_name="Unsorted Scores")
    
    # Save sorted Processor scores
    df_processor = pd.DataFrame(sorted_processor)
    df_processor.to_excel(writer, index=False, sheet_name="Sorted Processor")
    
    # Save sorted Memory scores
    df_memory = pd.DataFrame(sorted_memory)
    df_memory.to_excel(writer, index=False, sheet_name="Sorted Memory")
    
    # Save sorted Energy scores
    df_energy = pd.DataFrame(sorted_energy)
    df_energy.to_excel(writer, index=False, sheet_name="Sorted Energy")

print("Excel file 'node_scores.xlsx' has been created with unsorted and sorted scores.")
