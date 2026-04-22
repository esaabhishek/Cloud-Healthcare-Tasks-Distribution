from collections import Counter

counts = Counter()

with open("allocations_stage1_poisson_energy.csv") as file:   # save your dataset as tasks.csv
    next(file)  # skip header
    for line in file:
        node = line.strip().split(",")[-1]   # last column = assigned_node
        counts[node] += 1

print("\nTask count per node:\n")
for node, count in sorted(counts.items()):
    print(f"{node}: {count}")

# If cloud tasks exist, they would appear as "C" or "Cloud"
cloud = counts.get("Cloud", 0) + counts.get("C", 0)
print(f"\nTotal tasks sent to Cloud = {cloud}")
