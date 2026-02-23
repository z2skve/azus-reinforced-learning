import random
import json


class GeneticOptimizer:
    def __init__(self, pop_size=20) -> None:
        self.pop_size = pop_size
        self.last_best_score = None

        if self.last_best_score is not None:
            change = abs(current_best_score - self.last_best_score) / \
                (self.last_best_score + 1e-6)
            if change > 0.5:  # Umbral de anomalía
                is_anomaly = True
        self.gene_bounds = {
            "w_dead": (-100, -10),
            "w_alive": (0.0, 1.0),
            "w_expl_slope": (-0.2, 0.2),
            "w_expl_offset": (-1.0, 5.0),
            "w_bttm_expl": (-0.2, -3.0),
            "w_top_expl": (0.1, 5.0),
            "w_energy_action": (-0.05, -0.3),
            "w_energy_attack": (-0.3, -1.5),
            "w_deer_attack": (5.0, 15.0),
            "w_low_energy": (-0.5, -1.5),
            "w_low_health": (-0.1, -2.0),
            "w_high_hunger": (-0.05, -1.0),
            "w_closer_deer": (0.5, 2.5),
            "w_farther_deer": (-0.1, -1.1),
            "w_deer_close": (3.0, 7.0),
            "w_closer_monst": (-1.0, -3.0),
            "w_farther_monst": (0.1, 0.8),
        }

    def create_init_gen(self) -> None:
        """
        Creates initial genes for generation 0.
        """
        return [{name: random.uniform(b[0], b[1])
                 for name, b in self.gene_bounds.items()}
                for _ in range(self.pop_size)]

    def evolve(self, rated_genomes):
        rated_genomes.sort(key=lambda x: x[0], reverse=True)
        new_population = [rated_genomes[0][1], rated_genomes[1][1]]

        while len(new_population) < self.pop_size:
            p1, p2 = random.sample([g[1] for g in rated_genomes[:8]], 2)
            child = self._crossover(p1, p2)
            child = self._mutate(child)
            new_population.append(child)

        return new_population

    def _crossover(self, p1: dict, p2: dict):
        return {k: (p1[k] if random.random() > 0.5 else p2[k]) for k in p1}

    def _mutate(self, genome: dict):
        for k in genome:
            if random.random() < 0.1:  # Mutation chance
                genome[k] += random.uniform(-0.1, 0.1)
        return genome

    def save_checkpoint(self, population: list[dict, ...], gen_number: int,
                        filename=r"genetic-algorithm/genetic_checkpoint.json"):
        data = {
            "generation": gen_number,
            "population": population
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Saved optimizer on generation {gen_number}")

    def load_checkpoint(self, filename=r"genetic-algorithm/genetic_checkpoint.json") -> tuple[int, dict]:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            print(f"Checkpoint loaded. Continuing from Generation {
                  data['generation']}")
            return data["population"], data["generation"]

        except FileNotFoundError:
            print("No previous Generations found.")
            return None, 0
