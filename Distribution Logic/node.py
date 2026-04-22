import csv
import sys
from collections import OrderedDict

# ---------------------------
# Configurable parameters
# ---------------------------
NODES_CSV = "fog_node_stats_stage1_poisson_energy.csv"
TASKS_CSV = "allocations_stage1_poisson_energy.csv"
OUTPUT_CSV = "task_assignment_updated_prices.csv"

k_size = 1e-4   # influence of task size (per MB)
PRICE_FMT = "{:.12e}"

# ---------- Helpers ----------
def load_nodes(nodes_csv):
    """Load nodes.csv into OrderedDict: name -> {'base_price':float, 'op_cost':float}"""
    nodes = OrderedDict()
    try:
        with open(nodes_csv, newline='') as f:
            reader = csv.DictReader(f)
            if 'name' not in reader.fieldnames:
                raise RuntimeError("nodes.csv must contain 'name' column")
            for r in reader:
                name = r['name'].strip()
                # parse floats safely
                try:
                    base_price = float(r.get('base_price', 0.0) or 0.0)
                except:
                    base_price = 0.0
                try:
                    op_cost = float(r.get('operational_cost_per_cycle', 0.0) or 0.0)
                except:
                    op_cost = 0.0
                nodes[name] = {'base_price': base_price, 'op_cost': op_cost}
    except FileNotFoundError:
        print(f"Error: '{nodes_csv}' not found. Create it with the node parameter block you provided.")
        sys.exit(1)
    return nodes

def process_and_write(tasks_csv, nodes, output_csv):
    """Process tasks one-by-one, update node base_price, print concise lines, write CSV of results."""
    try:
        tasks_f = open(tasks_csv, newline='')
    except FileNotFoundError:
        print(f"Error: '{tasks_csv}' not found. Save your tasks as '{tasks_csv}'.")
        sys.exit(1)

    with tasks_f, open(output_csv, 'w', newline='') as out_f:
        reader = csv.DictReader(tasks_f)
        if 'assigned_node' not in reader.fieldnames:
            print("Error: tasks.csv must contain 'assigned_node' column.")
            sys.exit(1)

        writer = csv.writer(out_f)
        writer.writerow(['task_id','assigned_node','updated_price'])

        for row in reader:
            task_id = row.get('task_id','').strip()
            node = row.get('assigned_node','').strip()
            try:
                size_bytes = int(row.get('size_bytes') or 0)
            except:
                size_bytes = 0
            try:
                cycles = int(row.get('cycles') or 0)
            except:
                cycles = 0

            # ensure node exists; if not, initialize with small defaults
            if node not in nodes:
                nodes[node] = {'base_price': 1e-6, 'op_cost': 0.0}

            prev_price = nodes[node]['base_price']
            op_cost = nodes[node]['op_cost']

            # update rule
            delta = op_cost * cycles + k_size * (size_bytes / 1e6)
            new_price = prev_price + delta

            # store new price
            nodes[node]['base_price'] = new_price

            # print concise single-line output
            print(f"Task {task_id} -> {node} | updated price: {PRICE_FMT.format(new_price)}")

            # write CSV row
            writer.writerow([task_id, node, "{:.12e}".format(new_price)])

    print(f"\nFinished. Per-task updated prices written to: {output_csv}")

# ---------- Main ----------
def main():
    nodes = load_nodes(NODES_CSV)
    # Optional: print initial base prices summary (brief)
    print("Initial base prices (loaded from nodes.csv):")
    for n, info in nodes.items():
        print(f"  {n:>4} : {PRICE_FMT.format(info['base_price'])}")
    print("-" * 60)

    process_and_write(TASKS_CSV, nodes, OUTPUT_CSV)

if __name__ == "__main__":
    main()