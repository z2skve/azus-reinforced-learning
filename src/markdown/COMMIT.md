# Architecture Update: Transition from Collective to Individual Cognition

## Summary

This update introduces a fundamental shift in the agent architecture, moving from a shared "hive mind" model to decentralized individual learning. This change addresses a logic mismatch between the Genetic Algorithm (GA) and the Q-Learning brain, while introducing new mechanisms to prevent population stagnation.

---

## 1. Problem Identification: GA and Collective Brain Incompatibility

In the previous version, the system utilized a **Hive Mind** architecture. All individuals contributed to and drew from a single, shared **Q-Learning** brain. A Genetic Algorithm (GA) was used to select the best genomes (defining reward parameters) based on elitist selection.

### The Conflict

* **Collective Cognition:** The performance of an individual was not purely a result of its own genome, but rather a product of the collective values learned by the shared brain.
* **Selection Failure:** Because the evaluation tool measured collective interactions, it was impossible to isolate the fitness of a specific genome. Applying elitist selection to individuals sharing a single brain created a feedback loop where the GA could not accurately identify which specific genetic traits led to success.

---

## 2. Implementation: Individualized Q-Learning

To resolve the identification problem, the system has been refactored to grant each individual its own independent **Q-Learning brain**.

### Key Changes

* **Decentralized Learning:** Every agent now maintains its own Q-table. This allows the Genetic Algorithm to accurately map an individual's success to its specific genome.
* **Operation Optimization:** Despite the increased complexity of managing multiple brains, internal operations have been streamlined to reduce computational overhead per agent.
* **Impact on Convergence:** System-wide learning is now slower. Since agents no longer "share" failures instantly, the population requires more time to reach a consensus on optimal behaviors. However, this increases the robustness of the system by allowing diverse strategies to emerge simultaneously.

---

## 3. Genetic Diversity and Exploration

To combat premature convergence and ensure a wide range of behavioral interactions, the population structure has been modified:

* **20% Fresh Initialization:** In each generation, 20% of the population consists of entirely new individuals with randomized genomes (non-crossed).

