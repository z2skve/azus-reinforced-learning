import random
import json
import os


class QLearningBrain:
    """
    Handles the Q-Learning logic and memory for an autonomous agent.
    """

    def __init__(self, actions, learning_rate=0.1, discount_factor=0.95):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = 1.0
        self.epsilon_decay = 0.99995
        self.epsilon_min = 0.05
        self.q_table = {}

    def get_q_values(self, state: tuple) -> list:
        """Retrieves or initializes Q-values for a given state."""

        import types

        if isinstance(state, types.GeneratorType):
            print("Generator detected... Stopping")
            exit(0)

        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.actions)
        return self.q_table[state]

    def choose_action(self, state: tuple) -> int:
        """Selects an action index using an epsilon-greedy strategy."""

        if random.random() < self.epsilon:
            return random.randint(0, len(self.actions) - 1)

        q_values = self.get_q_values(state)
        return q_values.index(max(q_values))

    def learn(self, state: tuple, action: int, reward: float, next_state: tuple) -> None:
        """Updates the Q-table using the Bellman equation."""

        q_values = self.get_q_values(state)
        next_q_values = self.get_q_values(next_state)

        old_q = q_values[action]
        next_max = max(next_q_values)

        # Bellman Equation
        new_q = old_q + self.lr * (reward + self.gamma * next_max - old_q)
        self.q_table[state][action] = new_q

    def save_to_disk(self, filename: str):
        """Saves the Q-table and current epsilon to a JSON file."""
        # Convertimos las llaves (tuplas) a strings para JSON
        serializable_q = {str(k): v for k, v in self.q_table.items()}
        data = {
            "q_table": serializable_q,
            "epsilon": self.epsilon
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load_from_disk(self, filename: str):
        """Loads knowledge and epsilon from a file if it exists."""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                # Reconstruimos las tuplas a partir de los strings
                self.q_table = {eval(k): v for k, v in data["q_table"].items()}
                self.epsilon = data.get("epsilon", self.epsilon)
