######################################################################
#                            monster                                 #
######################################################################
import random
import pygame

from entity import Entity


class Monster(Entity):
    _base_image = None

    def __init__(self, name: str, x_pos: int, y_pos: int, map_dimension: tuple[int, int]) -> None:
        # Identifier
        self.name = name
        self.type = "Monster"

        # Agent Brain
        self.actions = ["UP", "DOWN", "LEFT", "RIGHT", "IDLE"]
        super().__init__(name, x_pos, y_pos,
                         map_dimension, self.type, self.actions)

        # Position
        self.current_cell: object = None

        # Miscellaneous
        self.hunger: int = random.randint(0, 30)
        self.closest_azu: tuple[int, int] = ()

        # Prey
        self.closest_azu: object = None
        self.target_dir = 0  # None

        # Load base image
        if Monster._base_image is None:
            Monster._base_image = pygame.Surface(
                (self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(Monster._base_image, (255, 0, 0),
                               (self.radius, self.radius), self.radius)

    def update(self, ui: object, dt: float, screen: pygame.Surface) -> None:
        new_cell = ui.get_cell_at_pos(self.pos)

        # Entity die
        if self.health <= 0:
            self.die(self, ui)
            reward: float = -100

            if self.last_state is not None:

                terminal_state: tuple[str, str] = ("DEAD", "DEAD")
                self.brain.learn(
                    self.last_state, self.last_action, reward, terminal_state)
            return

        # Change cell
        if new_cell != self.current_cell:
            if self.current_cell:
                self.current_cell.rm_entity(self)

            new_cell.add_entity(self)
            self.current_cell = new_cell

        # Brain decision
        neighbors = ui.get_neighbors(self, self.current_cell, self.radius)
        current_state = self._get_state(neighbors)
        action_idx = self.brain.choose_action(current_state)

        # Distance to prey
        if self.closest_azu:
            init_dist_azu = self.pos.distance_to(self.closest_azu.pos)

        # Brain execution
        self._execute_movement(action_idx, dt)

        # Reward management
        # ------------------------------------------------------------------ #
        reward: float = 0.1

        if self.hunger >= 50:
            reward -= 0.05

        if self.closest_azu:
            azu_pos = self.closest_azu.pos
            # Vector
            diff = azu_pos - self.pos
            if abs(diff.x) > abs(diff.y):
                self.target_dir = 3 if diff.x < 0 else 4
            else:
                self.target_dir = 1 if diff.y < 0 else 2

            act_dist_azu = self.pos.distance_to(azu_pos)

            if act_dist_azu < init_dist_azu:
                reward += 1.5
            else:
                reward -= 0.5

            if act_dist_azu <= 15:
                reward += 10

        if self.last_state is not None:
            self.brain.learn(self.last_state, self.last_action,
                             reward, current_state)

        self.last_state = current_state
        self.last_action = action_idx
        # ------------------------------------------------------------------ #

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(Monster._base_image, self.pos -
                    pygame.Vector2(self.radius, self.radius))

    def _execute_movement(self, action_idx: int, dt: float) -> None:
        """
        Translates the action index into physical movement.

        Args:
            action_idx: The index chosen by the brain.
            dt: Delta time for frame-independent movement.
        """
        direction: pygame.Vector2 = pygame.Vector2(0, 0)

        if action_idx == 0:
            direction.y = -1
        elif action_idx == 1:
            direction.y = 1
        elif action_idx == 2:
            direction.x = -1
        elif action_idx == 3:
            direction.x = 1
        else:
            pass  # IDLE

        # Normalize if needed
        if direction.length_squared() > 0:
            direction = direction.normalize()

        margin: int = 5

        speed_factor: float = (self.act_speed + self.acceleration * dt)
        self.pos += direction * speed_factor

        self.pos.x = max(margin, min(self.pos.x, self.map_width - margin))
        self.pos.y = max(margin, min(self.pos.y, self.map_height - margin))

    def _get_state(self, neighbors: tuple) -> tuple:
        """Converts environment data into a discrete state."""

        self.closest_azu = self._check_for_entities(
            "Azu", neighbors)[0]
        azu_near: int = 1 if self.closest_azu is not None else 0

        at_right: int = 1 if self.x > self.map_width - 5 else 0
        at_left: int = 1 if self.x < 5 else 0
        at_top: int = 1 if self.y < 5 else 0
        at_bottom: int = 1 if self.y > self.map_height - 5 else 0

        low_energy: int = 1 if self.act_energy > self.max_energy // 2 else 0

        return (azu_near, at_right, at_left,
                at_bottom, at_top, low_energy, self.target_dir)

    def _attack(self, closest_entity: object, dt: float):
        if (closest_entity.get_pos() - self.pos).length_squared() < 25:
            closest_entity.receive_damage(self.damage*dt)

        if object.type == "Azu":
            self.deer_damage += self.damage*dt

    def _balance_energy(self, dt: float) -> int:
        # Get health if not hungry
        if self.hunger < 100:
            self.hunger += dt
            self.health += dt
            self.health = min(self.health, self.max_health)
        else:
            self.hunger = max(self.hunger, 100)
            # self.health -= dt

        # XXX: Prob should adapt this behaviour
        if self.act_speed > self.max_speed//5 and self.act_energy > 0:
            self.act_energy -= self.act_speed//10 * dt
            self.act_energy = max(self.act_energy, 0)

        # If stopped gain energy
        elif self.act_speed == 0 and self.act_energy < self.max_energy:
            self.act_energy += 0.5
            self.act_energy = min(self.max_energy, self.act_energy)

        return self.act_energy

    def restart(self) -> None:
        self.alive = True
        self.health = self.max_health
        self.pos = pygame.Vector2(self.x, self.y)
        self.hunger = 0

    def get_info(self) -> str:
        return f"""
        Name : {self.name}
        ------------------
        Health : {self.health}
        Max Health : {self.max_health}
        Alive: {self.alive}
        Hunger : {self.hunger}
        Max Speed : {self.max_speed}
        Max Energy : {self.max_energy}
        Damage : {self.damage}
        ------------------
        Position : {self.current_cell}
        Closest prey : {self.closes_azu}

        """
