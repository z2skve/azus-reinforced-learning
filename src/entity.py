from abc import ABC, abstractmethod
from agent import QLearningBrain
import pygame
import random


class Entity(ABC):

    def __init__(self, name: str, x_pos: int, y_pos: int, map_dimension: tuple[int, int], entity_type: str, actions: list) -> None:
        self.map_width, self.map_height = map_dimension

        # Naming and Type
        self.name: str = name
        self.type: str = entity_type

        # Initial Position
        self.x: int = x_pos
        self.y: int = y_pos
        self.pos = pygame.Vector2(self.x, self.y)
        self.current_cell: object = None

        # Speed and Acceleration
        self.act_speed: int = 0
        self.max_speed: int = random.randint(18, 30)
        self.acceleration: int = random.randint(2, 6)
        # Health
        self.max_health: int = random.randint(70, 100)
        self.health: int = self.max_health
        self.alive: bool = True

        # Energy and Adrenaline
        self.max_energy: int = random.randint(70, 100)
        self.act_energy: int = self.max_energy

        # Miscellaneous
        self.damage: int = random.randint(6, 18)
        self.sight_range: int = random.randint(0, 100)

        # Draw options
        self.radius: int = 3

        # Agent Brain
        self.actions = actions
        self.brain = QLearningBrain(actions=list(range(len(self.actions))))
        self.last_state = None
        self.last_action = None

    @abstractmethod
    def update(self, ui: object, dt: float, screen: pygame.Surface) -> None:
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        pass

    @abstractmethod
    def _get_state(self, neighbors: tuple) -> tuple:
        pass

    @abstractmethod
    def get_info(self) -> str:
        pass

    def die(self, cell: tuple[int, int], ui: object) -> None:
        self.alive = False
        cell: object = ui.get_cell_at_pos(self.pos)
        cell.rm_entity(self)

    # Getters
    def get_name(self) -> str:
        return self.name

    def get_damage(self) -> int:
        return self.damage

    def get_pos(self) -> tuple[int, int]:
        return self.pos

    def get_grid(self) -> tuple:
        return self.current_cell

    def get_health(self):
        return self.health

    # Events
    def receive_dmg(self, damage: int, dt: float) -> None:
        self.health -= damage * dt
        if self.health <= 0:
            self.alive = False

    # Check Surroundings
    def _check_for_entities(self, obj_type: str, neighbors: tuple) -> tuple:
        """
        Finds the nearest entity of a specific type within a pixel radius.

        Args:
            obj_type: Target type identifier to filter (e.g., 'Monster').
            neighbors: Tuple with surrounding entities.

        Returns:
            A tuple (Entity, Distance) if found, otherwise (None, -1).
        """

        closest_entity = None
        min_dist_sq = self.sight_range ** 2

        for entity in neighbors:
            if entity.type == obj_type:
                dist_sq = (entity.pos - self.pos).length_squared()

                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_entity = entity

        if closest_entity:
            return closest_entity, min_dist_sq

        return None, -1
