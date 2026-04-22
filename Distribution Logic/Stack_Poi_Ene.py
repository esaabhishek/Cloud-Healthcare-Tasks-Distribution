import sys
import random
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import time

# -------------------- CONFIGURATION CONSTANTS -------------------- #
SLOT_DURATION = 1.0               # seconds per time slot
Y_CYCLES_PER_BIT = 1000           # cycles per bit
ETA_DELAY_COST = 1e-6
P_BASE_DEFAULT = 1e-6
KAPPA_PRICE_GAIN = 1e-5
CLOUD_PRICE_PER_CYCLE = 1e-3
SEED = 42

# Energy-MIPS pricing scale factors (tunable)
ALPHA = 1e-4   # scales unit_energy / MIPS contribution
BETA = 1e-7    # scales idle energy contribution

# File output names (poisson + energy version)
ALLOC_CSV = "allocations_stage1_poisson_energy.csv"
NODES_CSV = "fog_node_stats_stage1_poisson_energy.csv"
PLOT_PNG = "price_vs_load_poisson_energy.png"
JSON_LOG = "task_price_logs_poisson_energy.json"

# -------------------- NODES DATA & AHP -------------------- #
NODES_INFO = [
    {"name":"F1","Cores":6,"Min CPU Freq (GHz)":1.4,"Max CPU Freq (GHz)":2,"MIPS":12000,"Unit Energy (Processing) (J)":31,"Idle Energy (J)":7750,"RAM (GB)":10,"Secondary Mem (GB)":128,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F2","Cores":8,"Min CPU Freq (GHz)":1.8,"Max CPU Freq (GHz)":2.9,"MIPS":16000,"Unit Energy (Processing) (J)":33,"Idle Energy (J)":9000,"RAM (GB)":6,"Secondary Mem (GB)":128,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F3","Cores":8,"Min CPU Freq (GHz)":1.9,"Max CPU Freq (GHz)":3,"MIPS":17000,"Unit Energy (Processing) (J)":32,"Idle Energy (J)":11500,"RAM (GB)":4,"Secondary Mem (GB)":128,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F4","Cores":8,"Min CPU Freq (GHz)":3.2,"Max CPU Freq (GHz)":4.4,"MIPS":14000,"Unit Energy (Processing) (J)":34,"Idle Energy (J)":8500,"RAM (GB)":6,"Secondary Mem (GB)":128,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F5","Cores":6,"Min CPU Freq (GHz)":2.1,"Max CPU Freq (GHz)":4,"MIPS":18000,"Unit Energy (Processing) (J)":45,"Idle Energy (J)":13000,"RAM (GB)":6,"Secondary Mem (GB)":512,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F6","Cores":4,"Min CPU Freq (GHz)":1.1,"Max CPU Freq (GHz)":3.3,"MIPS":10000,"Unit Energy (Processing) (J)":30,"Idle Energy (J)":6500,"RAM (GB)":6,"Secondary Mem (GB)":64,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F7","Cores":4,"Min CPU Freq (GHz)":1.8,"Max CPU Freq (GHz)":3.5,"MIPS":15000,"Unit Energy (Processing) (J)":43,"Idle Energy (J)":10000,"RAM (GB)":8,"Secondary Mem (GB)":512,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F8","Cores":4,"Min CPU Freq (GHz)":3,"Max CPU Freq (GHz)":4.8,"MIPS":19000,"Unit Energy (Processing) (J)":48,"Idle Energy (J)":14500,"RAM (GB)":14,"Secondary Mem (GB)":512,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F9","Cores":8,"Min CPU Freq (GHz)":1.6,"Max CPU Freq (GHz)":3.2,"MIPS":20000,"Unit Energy (Processing) (J)":40,"Idle Energy (J)":14000,"RAM (GB)":6,"Secondary Mem (GB)":512,"Max RAM":14,"Max Secondary Mem":512},
    {"name":"F10","Cores":8,"Min CPU Freq (GHz)":1.8,"Max CPU Freq (GHz)":3.5,"MIPS":21000,"Unit Energy (Processing) (J)":39,"Idle Energy (J)":14200,"RAM (GB)":6,"Secondary Mem (GB)":512,"Max RAM":14,"Max Secondary Mem":512}
]

AHP_SCORES = {"F1":0.503304,"F2":0.417915,"F3":0.362192,"F4":0.697573,"F5":0.325451,"F6":0.657885,"F7":0.447843,"F8":0.422712,"F9":0.273881,"F10":0.300741}

# deterministic randomness
np.random.seed(SEED)
random.seed(SEED)

# -------------------- CLASSES -------------------- #
class FogNode:
    def __init__(self, info: Dict):
        self.name = info["name"]
        self.cores = info["Cores"]
        self.mips = info["MIPS"]
        # cycles per slot
        self.cap_per_slot = int(self.mips * 1e6 * SLOT_DURATION)
        self.admission_capacity = int(0.9 * self.cap_per_slot)
        self.queue = 0

        unit_energy = info.get("Unit Energy (Processing) (J)", 30.0)   # J (assumed unit)
        idle_energy = info.get("Idle Energy (J)", 0.0)               # J
        self.operational_cost_per_cycle = unit_energy / (self.mips * 1e6)

        self.base_price = P_BASE_DEFAULT + ALPHA * (unit_energy / max(1.0, self.mips)) + BETA * (idle_energy / 1e6)

        self.unit_energy = unit_energy
        self.idle_energy = idle_energy

        self.received_cycles = 0

        print(f"[Node Init] {self.name}: MIPS={self.mips}, UnitEnergy={unit_energy}, IdleEnergy={idle_energy}, "
              f"BasePrice={self.base_price:.9e}, OpCostPerCycle={self.operational_cost_per_cycle:.3e}")

    def current_load_fraction(self):
        return self.queue / max(1, self.cap_per_slot)

    def effective_capacity_left(self):
        return max(0, self.admission_capacity - self.queue)


class EEGTask:
    def __init__(self, tid:int, size_bytes:int, deadline:Optional[float]=None):
        self.id = tid
        self.size_bytes = size_bytes
        self.size_bits = size_bytes * 8
        self.cycles_required = int(self.size_bits * Y_CYCLES_PER_BIT)
        self.deadline = deadline
        self.assigned_node = None
        self.assigned_cycles = 0


class FogHead:
    def __init__(self, provider_nodes: List[FogNode], kappa:float=KAPPA_PRICE_GAIN):
        self.nodes = provider_nodes
        self.kappa = kappa
        self.prices = {n.name: n.base_price for n in provider_nodes}

    def update_prices_dynamic(self):
        new_prices = {}
        for n in self.nodes:
            frac = n.current_load_fraction()
            # dynamic price: base price + kappa * load fraction
            p = n.base_price + self.kappa * frac
            new_prices[n.name] = p
        self.prices = new_prices

    def broadcast_info(self):
        q = {n.name: n.queue for n in self.nodes}
        return self.prices.copy(), q

    def admit_task_to_node(self, node_name:str, cycles:int) -> bool:
        node = next(n for n in self.nodes if n.name == node_name)
        if node.effective_capacity_left() >= cycles:
            node.queue += cycles
            node.received_cycles += cycles
            return True
        return False

# -------------------- HELPERS -------------------- #
def compute_lambda_from_capacity(nodes_info, exclude_head_name, avg_task_bytes=20*1024, target_util=0.8):
    avg_task_bits = avg_task_bytes * 8
    cycles_per_task = avg_task_bits * Y_CYCLES_PER_BIT
    total_mips = sum(n["MIPS"] for n in nodes_info if n["name"] != exclude_head_name)
    total_cycles_per_sec = total_mips * 1e6
    lambda_tasks = (target_util * total_cycles_per_sec) / max(1, cycles_per_task)
    return lambda_tasks

def estimate_delay_for_offload(task: EEGTask, node: FogNode, R_bits_per_sec: float):
    O_j = node.cap_per_slot / max(1e-9, SLOT_DURATION)
    uplink_rate_in_cycles_per_sec = max(1e-9, R_bits_per_sec / Y_CYCLES_PER_BIT)
    uplink_time = task.cycles_required / uplink_rate_in_cycles_per_sec
    service_time = task.cycles_required / max(1e-9, O_j)
    queue_time = node.queue / max(1e-9, O_j)
    return uplink_time + service_time + queue_time

def follower_choose_node(task: EEGTask, fog_head: FogHead, R_rates: Dict, eta=ETA_DELAY_COST):
    prices, queues = fog_head.broadcast_info()
    best_node = None
    best_cost = float("inf")
    for node in fog_head.nodes:
        p = prices[node.name]
        Rbits = R_rates.get((task.id, node.name), 5e6)  # fallback 5 Mbps
        delay = estimate_delay_for_offload(task, node, Rbits)

        # Monetary cost = price * cycles
        monetary_cost = p * task.cycles_required

        # Optional: include a simple energy component to follower's perceived cost:
        # energy_cost = operational_cost_per_cycle (J per cycle) * cycles_required (J)
        # convert J to small monetary units via a tiny scaler if desired (omitted for now)
        # energy_cost = node.operational_cost_per_cycle * task.cycles_required

        # Delay cost = eta * delay
        delay_cost = eta * delay

        total_cost = monetary_cost + delay_cost

        if node.effective_capacity_left() < task.cycles_required:
            total_cost = float("inf")

        if total_cost < best_cost:
            best_cost = total_cost
            best_node = node
    if best_node is None:
        return None, None
    return best_node.name, best_cost

# -------------------- MAIN SIMULATION -------------------- #
def run_stage1_stackelberg_poisson_energy(folder_path: str, save_dir: str = ".",
                                          target_util: float = 0.8,
                                          slot_duration: float = SLOT_DURATION):
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # 1) Read all files in the folder -> tasks list (we will draw arrivals from this pool)
    file_list = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    file_list.sort()  # consistent ordering
    total_files = len(file_list)
    tasks_pool = []
    for idx, fname in enumerate(file_list, start=1):
        size_bytes = os.path.getsize(os.path.join(folder_path, fname))
        tasks_pool.append( (idx, fname, size_bytes) )

    if total_files == 0:
        print("No files found in folder. Exiting.")
        return {}

    # 2) Setup fog nodes & select fog head by AHP scores
    all_nodes = [FogNode(info) for info in NODES_INFO]
    fog_head_name = max(AHP_SCORES, key=AHP_SCORES.get)
    provider_nodes = [n for n in all_nodes if n.name != fog_head_name]

    # 3) Compute lambda from capacity and chosen target utilization
    lambda_tasks_per_sec = compute_lambda_from_capacity(NODES_INFO, fog_head_name,
                                                        avg_task_bytes=20*1024,
                                                        target_util=target_util)
    lam_per_slot = lambda_tasks_per_sec * slot_duration

    # Print selected fog head and arrival rate
    print("-" * 60)
    print(f"Selected fog head (leader) by AHP: {fog_head_name}")
    print(f"Computed λ (Poisson arrival rate): {lambda_tasks_per_sec:.6f} tasks/sec")
    print(f"Per-slot λ (lam_per_slot) with slot_duration={slot_duration}s: {lam_per_slot:.6f} arrivals/slot")
    print(f"Total tasks in folder to process: {total_files}")
    print("-" * 60)

    # 4) Initialize fog head and synthetic initial queues (0..30% of cap) and uplink rates
    for n in provider_nodes:
        n.queue = random.randint(0, int(0.3 * n.cap_per_slot))

    fog_head = FogHead(provider_nodes, kappa=KAPPA_PRICE_GAIN)
    fog_head.update_prices_dynamic()

    # Synthetic uplink rates per (taskid, node) - we'll update when tasks arrive
    R_rates = {}

    # 5) Simulation loop: process until all tasks from folder are consumed
    remaining_idx = 0   # index into tasks_pool
    slot = 0
    task_price_logs = []
    allocations = []

    start_time = time.time()
    while remaining_idx < total_files:
        slot += 1
        # draw number of arrivals this slot
        arrivals_this_slot = np.random.poisson(lam=lam_per_slot)
        # cap arrivals by remaining tasks in folder
        arrivals_this_slot = min(arrivals_this_slot, total_files - remaining_idx)
        # If no arrivals, show idle info and continue
        if arrivals_this_slot == 0:
            if slot % 10 == 0:
                print(f"Slot {slot}: idle (no arrivals). Remaining tasks: {total_files - remaining_idx}")
            # still update prices to reflect changing loads
            fog_head.update_prices_dynamic()
            continue

        # process each arrival as a task drawn from tasks_pool in order
        for a in range(arrivals_this_slot):
            remaining_idx += 1
            tid, fname, size_bytes = tasks_pool[remaining_idx - 1]
            task = EEGTask(tid=tid, size_bytes=size_bytes)

            # create synthetic uplink rates for this task to each provider node (5-50 Mbps)
            for n in provider_nodes:
                mbps = random.uniform(5, 50)
                R_rates[(task.id, n.name)] = mbps * 1e6

            # Leader updates prices before the follower decision (Stackelberg)
            fog_head.update_prices_dynamic()
            prices, queues = fog_head.broadcast_info()

            # Follower chooses node (minimize monetary + delay cost)
            assigned_node_name, predicted_cost = follower_choose_node(task, fog_head, R_rates)

            # Log decision snapshot (before admission)
            task_log = {
                "slot": slot,
                "task_id": task.id,
                "file_name": fname,
                "size_bytes": task.size_bytes,
                "prices_at_decision": {n: round(p, 12) for n,p in prices.items()},
                "queues_at_decision": queues,
                "assigned_node_candidate": assigned_node_name,
                "predicted_cost": predicted_cost
                
            }

            # Try to admit to the chosen node
            if assigned_node_name is None:
                task.assigned_node = "CLOUD"
                task.assigned_cycles = task.cycles_required
                task_log["assigned_node_final"] = "CLOUD"
                task_log["assignment_result"] = "sent_to_cloud (no node had capacity)"
            else:
                accepted = fog_head.admit_task_to_node(assigned_node_name, task.cycles_required)
                if accepted:
                    task.assigned_node = assigned_node_name
                    task.assigned_cycles = task.cycles_required
                    task_log["assigned_node_final"] = assigned_node_name
                    task_log["assignment_result"] = "accepted"
                else:
                    task.assigned_node = "CLOUD"
                    task.assigned_cycles = task.cycles_required
                    task_log["assigned_node_final"] = "CLOUD"
                    task_log["assignment_result"] = "sent_to_cloud (node lacked capacity at admission)"

            task_price_logs.append(task_log)
            allocations.append((task.id, fname, task.size_bytes, task.size_bits, task.cycles_required, task.assigned_node))

        # end of arrivals_this_slot
        # update prices after the batch
        fog_head.update_prices_dynamic()

        # print progress summary per slot
        print(f"Slot {slot}: arrivals={arrivals_this_slot}, processed total so far={remaining_idx}/{total_files}")

    # end while -> all tasks processed
    elapsed = time.time() - start_time
    print("-" * 60)
    print(f"Simulation completed in {slot} slots, elapsed {elapsed:.2f}s. All tasks processed ({total_files}).")

    # Save JSON log
    json_out = os.path.join(save_dir, JSON_LOG)
    with open(json_out, "w") as f:
        json.dump(task_price_logs, f, indent=4)
    print(f"Saved task decision JSON: {json_out}")

    # Build DataFrames and save CSVs
    alloc_df = pd.DataFrame(allocations, columns=["task_id", "file_name", "size_bytes", "size_bits", "cycles", "assigned_node"])
    node_stats = []
    for n in provider_nodes:
        node_stats.append({
            "name": n.name,
            "initial_queue_fraction": round(n.queue / max(1, n.cap_per_slot), 6),
            "received_cycles": n.received_cycles,
            "cap_per_slot": n.cap_per_slot,
            "admission_capacity": n.admission_capacity,
            "final_queue": n.queue,
            "base_price": n.base_price,
            "operational_cost_per_cycle": n.operational_cost_per_cycle
        })
    nodes_df = pd.DataFrame(node_stats).sort_values("name")
    alloc_out = os.path.join(save_dir, ALLOC_CSV)
    nodes_out = os.path.join(save_dir, NODES_CSV)
    plot_out = os.path.join(save_dir, PLOT_PNG)

    alloc_df.to_csv(alloc_out, index=False)
    nodes_df.to_csv(nodes_out, index=False)
    print(f"Saved allocations CSV: {alloc_out}")
    print(f"Saved node stats CSV: {nodes_out}")

    # Plot price vs load (using final prices)
    prices_after = fog_head.prices.copy()
    plt.figure(figsize=(10,6))
    names = nodes_df["name"].tolist()
    prices_list = [prices_after[n] for n in names]
    loads = nodes_df["received_cycles"].tolist()
    plt.scatter(prices_list, loads)
    for i, name in enumerate(names):
        plt.text(prices_list[i], loads[i], name)
    plt.xlabel("Price per cycle (units)")
    plt.ylabel("Received cycles (load)")
    plt.title(f"Fog Nodes: price vs load after Stage-1 offloading (head={fog_head_name}) (energy-aware)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(plot_out)
    plt.close()
    print(f"Saved plot: {plot_out}")

    summary = {
        "fog_head": fog_head_name,
        "num_tasks": total_files,
        "alloc_csv": alloc_out,
        "nodes_csv": nodes_out,
        "plot_png": plot_out,
        "json_log": json_out,
        "alloc_df": alloc_df,
        "nodes_df": nodes_df,
        "prices_after": prices_after
    }
    return summary

# -------------------- ENTRY POINT -------------------- #
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stage1_stackelberg_poisson_energy.py /path/to/Signals_2020_txt")
        sys.exit(1)

    folder_path = sys.argv[1]
    out = run_stage1_stackelberg_poisson_energy(folder_path, save_dir=".")
    print(f"AHP-selected fog head: {out['fog_head']}")
    print(f"Total tasks processed: {out['num_tasks']}")
    print(f"Saved allocations CSV: {out['alloc_csv']}")
    print(f"Saved node stats CSV: {out['nodes_csv']}")
    print(f"Saved JSON log: {out['json_log']}")
    print(f"Saved plot PNG: {out['plot_png']}")
