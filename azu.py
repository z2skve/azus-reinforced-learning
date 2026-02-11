######################################################################
#                               azu                                  #
######################################################################

import random
import pygame

from entity import Entity


class Azu(Entity):
    _base_image = None
    knowledge = {}

    def __init__(self, name: str, x_pos: int, y_pos: int, map_dimension: tuple[int, int]) -> None:
        # Agent Brain
        self.type: str = "Azu"
        self.actions = ["UP", "DOWN", "LEFT", "RIGHT", "IDLE"]
        super().__init__(name, x_pos, y_pos,
                         map_dimension, self.type, self.actions)

        # Knowledge
        self.brain.q_table: dict = Azu.knowledge
        self.top_reward: float = 0

        # Adrenaline
        self.max_adrenaline: int = self.max_energy * 2
        self.act_adrenaline: int = self.max_adrenaline

        # Miscellaneous
        self.hunger: int = random.randint(0, 30)

        # Prey
        self.damage_dealt_deer = 0
        self.closest_deer: object = None
        self.target_dir: int = 0

        # Monster
        self.closest_monster: object = None
        self.monster_dir: int = 0

        # Load base image
        if Azu._base_image is None:
            Azu._base_image = pygame.Surface(
                (self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(Azu._base_image, (39, 200, 245),
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
        init_dist_deer = init_dist_monster = float('inf')
        if self.closest_deer:
            init_dist_deer = self.pos.distance_to(self.closest_deer.pos)
        if self.closest_monster:
            init_dist_monster = self.pos.distance_to(self.closest_monster.pos)

        # Brain execution
        self._execute_movement(action_idx, dt)

        self.manage_reward(current_state, action_idx, dt,
                           init_dist_monster, init_dist_deer)

    def manage_reward(self, current_state: tuple, action_idx: int, dt: float,
                      init_dist_monster: float, init_dist_deer: float) -> None:
        # ------------------------------------------------------------------ #
        # Alive reward (avoid depression)
        reward: float = 0.1

        # Hunger penalty
        if self.hunger >= 50:
            reward -= 0.05

        # Energy penalty
        if self.act_energy <= 0:
            reward -= 1

        # ENTITY BASED REWARDS
        # - - - - - - - - - - - - - - - - - - - - - - - - -
        # Deer based rewards
        if self.closest_deer:
            deer_pos = self.closest_deer.pos

            # Closest deer location
            diff = deer_pos - self.pos
            if abs(diff.x) > abs(diff.y):
                self.target_dir = 3 if diff.x < 0 else 4
            else:
                self.target_dir = 1 if diff.y < 0 else 2

            act_dist_deer = self.pos.distance_to(deer_pos)

            # Closer to deer reward
            if act_dist_deer < init_dist_deer:
                reward += 1.5
            else:
                reward -= 0.5

            # Face-to-face deer reward
            if act_dist_deer <= 15:
                reward += 10
                self.hunger -= dt * 2
                self.hunger = max(self.hunger, 0)

        # Monster based rewards
        if self.closest_monster:
            monster_pos = self.closest_monster.pos

            # Closest monster location
            diff = monster_pos - self.pos
            if abs(diff.x) > abs(diff.y):
                self.monster_dir = 3 if diff.x < 0 else 4
            else:
                self.monster_dir = 1 if diff.y < 0 else 2

            # Closer to monster penalty
            act_dist_monster = self.pos.distance_to(self.closest_monster.pos)
            if act_dist_monster > init_dist_monster:
                reward += 1.5
            else:
                reward -= 2
        # - - - - - - - - - - - - - - - - - - - - - - - - -

        if self.last_state is not None:
            self.brain.learn(self.last_state, self.last_action,
                             reward, current_state)

        self.last_state = current_state
        self.last_action = action_idx

        self.top_reward = max(self.top_reward, reward)
        # ------------------------------------------------------------------ #

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(Azu._base_image, self.pos -
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
            self.act_energy -= dt
        else:
            self.act_energy += 0.8 * dt
        self.act_energy = max(0, min(self.max_energy, self.act_energy))

        # Manage border positions
        self.pos.x = max(margin, min(self.pos.x, self.map_width - margin))
        self.pos.y = max(margin, min(self.pos.y, self.map_height - margin))

    def set_hunger(self, hunger: int) -> None:
        self.hunger = hunger

    def reset_deer_dmg(self) -> None:
        self.deer_damage = 0

    # Getters
    def _get_state(self, neighbors: tuple) -> tuple:
        """Converts environment data into a discrete state."""

        self.closest_monster = self._check_for_entities(
            "Monster", neighbors)[0]
        monster_near: int = 1 if self.closest_monster is not None else 0

        self.closest_deer = self._check_for_entities("Deer", neighbors)[0]
        deer_near: int = 1 if self.closest_deer is not None else 0

        at_right: int = 1 if self.x > self.map_width - 5 else 0
        at_left: int = 1 if self.x < 5 else 0
        at_top: int = 1 if self.y < 5 else 0
        at_bottom: int = 1 if self.y > self.map_height - 5 else 0

        low_energy: int = 1 if self.act_energy > self.max_energy // 2 else 0

        hunger_status: int = 1 if self.hunger > 50 else 0

        return (monster_near, deer_near, hunger_status, at_right, at_left,
                at_bottom, at_top, low_energy, self.target_dir, self.monster_dir)

    # Events

    def _attack(self, closest_entity: object, dt: float):
        if (closest_entity.get_pos() - self.pos).length_squared() < 25:
            closest_entity.receive_damage(self.damage*dt)

        if object.type == "Deer":
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
        Actual Speed : {self.act_speed}
        Max Speed : {self.max_speed}
        Actual Energy : {self.act_energy}
        Max Energy : {self.max_energy}
        Max Adrenaline : {self.max_adrenaline}
        Damage : {self.damage}
        Sight Range : {self.sight_range}
        ------------------
        Position : {self.pos}
        Closest Deer : {self.closest_deer}
        Closest Monster : {self.closest_monster}
        Last Action : {self.last_action}
        ------------------
        Top Reward : {self.top_reward}

        """
