######################################################################
#                               deer                                 #
######################################################################

import random
import pygame

from entity import Entity


class Deer(Entity):
    _base_image = None
    knowledge = {}

    INF = float("inf")

    def __init__(self, name: str, x_pos: int, y_pos: int, map_dimension: tuple[int, int], num_grids: int) -> None:
        # Identifier
        self.name = name
        self.type = "Deer"

        # Agent Brain
        self.actions = ["UP", "DOWN", "LEFT", "RIGHT", "IDLE"]
        super().__init__(name, x_pos, y_pos,
                         map_dimension, num_grids, self.type, self.actions)

        # Knowledge
        self.brain.q_table: dict = Deer.knowledge

        # Energy
        self.max_energy = random.randint(80, 120)

        # Position
        self.current_cell: object = None

        # Adrenaline
        self.max_adrenaline: int = self.max_energy * 2
        self.act_adrenaline: int = self.max_adrenaline

        # Hunter
        self.closest_azu: object = None
        self.azu_too_close: int = 0
        self.azu_dir: int = 0

        # Load base image
        if Deer._base_image is None:
            Deer._base_image = pygame.Surface(
                (self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(Deer._base_image, (255, 255, 0),
                               (self.radius, self.radius), self.radius)

    def _balance_energy(self, dt: float) -> int:
        # XXX: Prob should adapt this behaviour
        if self.act_speed > self.max_speed//5 and self.act_energy > 0:
            self.act_energy -= self.act_speed//10 * dt
            self.act_energy = max(self.act_energy, 0)

        # If stopped gain energy
        elif self.act_speed == 0 and self.act_energy < self.max_energy:
            self.act_energy += 0.5
            self.act_energy = min(self.max_energy, self.act_energy)

        return self.act_energy

    def update(self, ui: object, dt: float) -> None:
        new_cell = ui.get_cell_at_pos(self.pos)

        # Entity die
        if self.health <= 0:
            self.die(self, ui)
            self.reward: float = -20
            if self.last_state is not None:
                terminal_state: tuple[str, ...] = tuple(
                    "DEAD" for _ in range(len(self.actions)))
                self.brain.learn(self.last_state, self.last_action,
                                 self.reward, terminal_state)
            return

        # Change cell
        if new_cell != self.current_cell:
            if self.current_cell:
                self.current_cell.rm_entity(self)

            new_cell.add_entity(self)
            self.current_cell = new_cell

        # Distance to prey
        if self.closest_azu:
            init_dist_azu = self.pos.distance_to(self.closest_azu.pos)
            if init_dist_azu < 10:
                self.azu_too_close = 1
                self.reward -= 3
        else:
            init_dist_azu = Deer.INF

        # Brain decision
        neighbors = ui.get_neighbors(self, self.current_cell, self.radius)
        current_state = self._get_state(neighbors)
        action_idx = self.brain.choose_action(current_state)

        # Brain execution
        self._execute_movement(action_idx, dt)

        # Manage energy
        # self.act_energy = self._balance_energy(dt)

        # Reward management
        # ------------------------------------------------------------------ #
        self.reward: float = 0.1

        # Action penalty
        if action_idx < 4:
            self.reward -= 0.05

        self.azu_too_close = 0
        if self.closest_azu:
            azu_pos = self.closest_azu.pos
            # Vector
            diff = azu_pos - self.pos
            if abs(diff.x) > abs(diff.y):
                self.azu_dir = 3 if diff.x < 0 else 4
            else:
                self.azu_dir = 1 if diff.y < 0 else 2

            act_dist_azu = self.pos.distance_to(azu_pos)

            if act_dist_azu > init_dist_azu:
                self.reward += 0.5
            else:
                self.reward -= 2

        if self.last_state is not None:
            self.brain.learn(self.last_state, self.last_action,
                             self.reward, current_state)

        self.last_state = current_state
        self.last_action = action_idx

        # ------------------------------------------------------------------ #

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(Deer._base_image, self.pos -
                    pygame.Vector2(self.radius, self.radius))

    def _execute_movement(self, action_idx: int, dt: float) -> None:
        """
        Translates the action index into physical movement.

        Args:
            action_idx: The index chosen by the brain.
            dt: Delta time for frame-independent movement.
        """
        direction: pygame.Vector2 = pygame.Vector2(0, 0)

        # Clockwise
        if action_idx == 0:
            direction.y = -1
        elif action_idx == 1:
            direction.x = 1
        elif action_idx == 2:
            direction.y = 1
        elif action_idx == 3:
            direction.x = -1

        # IDLE
        elif action_idx == 4:
            pass

        if direction.length_squared() > 0:
            direction = direction.normalize()

        margin: int = 5

        speed_factor: float = (self.act_speed + self.acceleration * dt)

        # Manage energy movement
        if self.act_energy > 0:
            self.pos += direction * speed_factor

        # Manage energy consume
        if direction != (0, 0):
            self.act_energy -= dt * 1.5
        else:
            self.act_energy += 0.8 * dt
        self.act_energy = max(0, min(self.max_energy, self.act_energy))

        # Manage border positions
        self.pos.x = max(margin, min(self.pos.x, self.map_width - margin))
        self.pos.y = max(margin, min(self.pos.y, self.map_height - margin))

    def _get_state(self, neighbors: tuple) -> tuple:
        """Converts environment data into a discrete state."""

        self.closest_azu = self._check_for_entities("Azu", neighbors)[0]
        azu_near: int = 1 if self.closest_azu is not None else 0

        tmp_margin = 7
        at_right: int = 1 if self.x > self.map_width - tmp_margin else 0
        at_left: int = 1 if self.x < tmp_margin else 0
        at_top: int = 1 if self.y < tmp_margin else 0
        at_bottom: int = 1 if self.y > self.map_height - tmp_margin else 0

        low_energy: int = 1 if self.act_energy < self.max_energy // 2 else 0

        return (azu_near, at_right, at_left,
                at_bottom, at_top, low_energy, self.azu_dir, self.azu_too_close)

    def restart(self) -> None:
        self.alive = True
        self.health = self.max_health
        self.hunger = 0
        self.pos.x = random.randint(10, self.map_width - 10)
        self.pos.y = random.randint(10, self.map_height - 10)

    def get_info(self) -> str:
        return f"""
        Name : {self.name}
        ------------------
        Health : {self.health}
        Max Health : {self.max_health}
        Alive: {self.alive}
        Max Speed : {self.max_speed}
        Max Energy : {self.max_energy}
        Max Adrenaline : {self.max_adrenaline}
        Damage : {self.damage}
        ------------------
        Position : {self.current_cell}

        """
