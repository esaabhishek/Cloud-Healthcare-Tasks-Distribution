# Energy-Aware Fog Node Selection using AHP

## Project Overview
This repository implements a complete multi-criteria decision-making pipeline for selecting the most suitable fog node using the Analytic Hierarchy Process (AHP). The selection is based on processor capability, memory availability, and energy efficiency, and is intended to support fog-head (leader) selection in energy-aware fog computing and Stackelberg-based task offloading systems.

---

## Workflow
Raw Fog Node Specifications  
→ Group Score Computation  
→ Score Normalization  
→ AHP Weight Calculation  
→ Final AHP Score  
→ Optimal Fog Node Selection  

---

## Repository Structure
- GroupScore.py – Computes raw processor, memory, and energy scores  
- Normalization.py – Normalizes all scores to a [0,1] scale  
- Aczel_AHP.py – AHP weight computation using geometric mean method  
- DD.py – AHP using a custom decision matrix  
- sorted_scores.json – Raw and sorted group scores  
- normalized.json – Normalized scores  
- ahp_scores.json – Final AHP scores (geometric mean method)  
- DD_ahp_results.json – Final AHP scores (custom matrix)  
- *.xlsx – Excel reports generated at each stage  

---

## 1. GroupScore.py – Group Score Computation
Purpose:
Calculates raw performance metrics for each fog node using hardware specifications.

Scores computed:
- Processor Score: derived from average CPU frequency and MIPS
- Memory Score: weighted combination of RAM and secondary storage
- Energy Score: total operational, computational, and idle energy

Outputs:
- sorted_scores.json
- node_Groupscores.xlsx

---

## 2. Normalization.py – Score Normalization
Purpose:
Transforms heterogeneous scores into a comparable [0,1] range.

Method:
- Processor & Memory: min–max normalization
- Energy: reverse min–max normalization (lower energy is better)

Outputs:
- normalized.json
- normalized.xlsx

---

## 3. Aczel_AHP.py – AHP using Geometric Mean
Purpose:
Computes criteria weights using pairwise comparison matrices and geometric mean (Aczél method).

Steps:
- Define pairwise matrices for Processor, Memory, Energy
- Compute geometric mean-based weights
- Calculate final AHP score per node

Output:
- ahp_scores.json
- ahp_results.xlsx

---

## 4. DD.py – AHP using Custom Decision Matrix
Purpose:
Alternative AHP approach using a predefined decision matrix based on domain or empirical knowledge.

Steps:
- Normalize decision matrix
- Compute row-average weights
- Apply weighted sum to normalized node scores

Output:
- DD_ahp_results.json
- DD_ahp_results.xlsx

---

## Final Selection
The fog node with the highest AHP score is selected as the Fog Head (Leader), offering the best trade-off between computation power, memory availability, and energy efficiency.

---

## How to Run
Execute the scripts in the following order:

python GroupScore.py  
python Normalization.py  
python Aczel_AHP.py  

or alternatively:

python DD.py  

---

## Application Context
This module supports:
- Fog head election
- Energy-aware scheduling
- Stackelberg game-based task offloading
- Delay- and energy-sensitive fog computing systems

---

## Reference
T. L. Saaty, The Analytic Hierarchy Process, McGraw-Hill, 1980.
