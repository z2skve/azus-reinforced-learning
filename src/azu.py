######################################################################
#                               azu                                  #
######################################################################

import random
import pygame

from entity import Entity


class Azu(Entity):
    _base_image = None

    INF = float("inf")
    MIN_ATTACK_ENERGY: int = 7

    def __init__(self, name: str, x_pos: int, y_pos: int,
                 map_dimension: tuple[int, int], num_grids: int,
                 brain: object, genome: dict) -> None:
        # Agent Brain
        self.type: str = "Azu"
        self.actions = ["UP", "DOWN", "LEFT", "RIGHT", "IDLE", "ATTACK"]
        super().__init__(name, x_pos, y_pos,
                         map_dimension, num_grids, self.type, self.actions)

        # Brain
        self.brain: object = brain

        # Rewards
        self.reward: int = 0
        # ~ Reward Values
        self.genome: dict = genome

        # Fitness vars
        self.deer_attacks = 0
        self.ticks_lived = 0

        # Visited Cells
        self.visited_cells = [0 for _ in range(
            self.map_grids * self.map_grids)]

        # Adrenaline
        self.max_adrenaline: int = self.max_energy * 2
        self.act_adrenaline: int = self.max_adrenaline

        # Miscellaneous
        self.hunger: int = random.randint(0, 10)
        self.last_check: int = 0

        # Prey
        # ...................................... #
        self.closest_deer: object = None
        self.target_dir: int = 0

        # ~ Binary, 0 or 1 to feed it to the state function
        self.is_deer_in_range: int = 0
        # ...................................... #

        # Monster
        self.closest_monster: object = None
        self.monster_dir: int = 0

        # Attack
        self.can_attack: int = 1

        # Explore
        self.closest_unknown: int = 0
        self.sight_range: int = random.randint(90, 150)
        self.cell_radius: int = 3

        # Load base image
        if Azu._base_image is None:
            Azu._base_image = pygame.Surface(
                (self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(Azu._base_image, (39, 200, 245),
                               (self.radius, self.radius), self.radius)

    def update(self, ui: object, dt: float) -> None:
        new_cell = ui.get_cell_at_pos(self.pos)

        # Set Reward to 0
        self.reward = 0

        # Entity die
        if self.health <= 0:
            self.die(self, ui)
            self.reward += self.genome["w_dead"]
            if self.last_state is not None:
                terminal_state: tuple[str, ...] = tuple(
                    "DEAD" for _ in range(len(self.actions)))
                self.brain.learn(
                    self.last_state, self.last_action, self.reward, terminal_state)
            return
        else:
            self.ticks_lived += 1

        # Change cell
        if new_cell != self.current_cell:
            if self.current_cell:
                self.current_cell.rm_entity(self)

            new_cell.add_entity(self)
            self.current_cell = new_cell

            # Exploration management
            self.closest_unknown = self.get_unexplored()

        # Energy management
        self._balance_hunger(dt)
        self.can_attack = 1 if self.act_energy >= Azu.MIN_ATTACK_ENERGY else 0

        # Brain decision
        neighbors = ui.get_neighbors(self, self.current_cell, self.cell_radius)
        current_state = self._get_state(neighbors)
        action_idx = self.brain.choose_action(current_state)

        # Distance to prey
        init_dist_deer = init_dist_monster = Azu.INF
        if self.closest_deer:
            init_dist_deer = self.pos.distance_to(self.closest_deer.pos)
        else:
            # Is close enought to attack
            self.is_deer_in_range = 0
            self.target_dir = 0

        if self.closest_monster:
            init_dist_monster = self.pos.distance_to(self.closest_monster.pos)

        # Brain execution
        self._execute_movement(action_idx, dt)

        # Manage rewards
        self.misc_rewards(current_state, action_idx, dt, init_dist_monster,
                          init_dist_deer)

        # Learn
        if self.last_state is not None:
            self.brain.learn(self.last_state, self.last_action,
                             self.reward, current_state)

        # Update state variables
        self.last_state = current_state
        self.last_action = action_idx

    def _explore_reward(self, cell_value: int) -> None:
        avrg: float = sum(self.visited_cells) / len(self.visited_cells) + 1

        # Formula attempt not working
        # cell_max = max(min(((avrg / (cell_value + 1)) *
        # (avrg - cell_value) / 2) + 1 / 2, 5), -0.2)

        # Formula did work
        k_slope = self.genome['w_expl_slope']
        offset = self.genome['w_expl_offset']

        cell_rw = max(min(k_slope * (cell_value - avrg)**3 +
                          offset, self.genome['w_bttm_expl']),
                      self.genome['w_top_expl'])

        self.reward += cell_rw

    def get_unexplored(self) -> int:
        """
        Returns the direction of the least visited surrounding cell
        """
        cell_x, cell_y = self.current_cell.get_pos()
        cell_position = cell_y * self.map_grids + cell_x

        self._explore_reward(self.visited_cells[cell_position])

        self.visited_cells[cell_position] += 1

        #                 ~ Top ~ Right ~ Bottom ~ Left ~
        around_cells = [Azu.INF, Azu.INF, Azu.INF, Azu.INF]
        if cell_y != 0:
            top = cell_position - self.map_grids
            top_cell_val = self.visited_cells[top]
            around_cells[0] = top_cell_val
        if cell_x != self.map_grids - 1:
            right = cell_position + 1
            right_cell_val = self.visited_cells[right]
            around_cells[1] = right_cell_val
        if cell_y != self.map_grids - 1:
            bottom = cell_position + self.map_grids
            bottom_cell_val = self.visited_cells[bottom]
            around_cells[2] = bottom_cell_val
        if cell_x != 0:
            left = cell_position - 1
            left_cell_val = self.visited_cells[left]
            around_cells[3] = left_cell_val

        min_value = min(around_cells)
        least_visited_cells = [i for i, val in enumerate(
            around_cells) if val == min_value]

        return random.choice(least_visited_cells)

    def misc_rewards(self, current_state: tuple, action_idx: int, dt: float,
                     init_dist_monster: float, init_dist_deer: float) -> None:
        # ------------------------------------------------------------------ #
        # Alive reward (avoid depression)
        self.reward += self.genome['w_alive']

        # Action penalty
        if action_idx < 4:
            self.reward += self.genome['w_energy_action']
        elif action_idx == 5 and self.can_attack == 1:  # Attack
            self.reward += self.genome['w_energy_attack']

            # Attack successful reward
            if self.is_deer_in_range == 1:
                self.reward += self.genome['w_deer_attack']
                self.hunger = max(min(self.hunger - self.damage, 50), 0)

        # Hunger penalty
        if self.hunger >= 50:
            self.reward += self.genome['w_high_hunger']

        # Energy penalty
        if self.act_energy <= 0:
            self.reward += self.genome['w_low_energy']

        # Health penalty
        if self.health <= self.max_health // 2:
            self.reward += self.genome['w_low_health']

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
                self.reward += self.genome['w_closer_deer']
            else:
                self.reward += self.genome['w_farther_deer']

            # Face-to-face deer reward
            if act_dist_deer <= 10:
                self.reward += self.genome['w_deer_close']

                self.is_deer_in_range = 1
            else:
                self.is_deer_in_range = 0

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
                self.reward += self.genome['w_farther_monst']
            else:
                self.reward += self.genome['w_closer_monst']

        # - - - - - - - - - - - - - - - - - - - - - - - - -
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
        # Attack
        elif action_idx == 5:
            if self.can_attack == 1:
                self.act_energy -= Azu.MIN_ATTACK_ENERGY * dt
                if self.is_deer_in_range == 1:
                    self.closest_deer.receive_dmg(self.damage, dt)
                    self.deer_attacks += 1

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

    # Getters
    def get_reward(self) -> None:
        return self.reward

    def _get_state(self, neighbors: tuple) -> tuple:
        """Converts environment data into a discrete state."""

        self.last_check += 1
        if self.last_check == 2:
            self.last_check = 0

            self.closest_monster = self._check_for_entities(
                "Monster", neighbors)[0]
            self.closest_deer = self._check_for_entities("Deer", neighbors)[0]

        monster_near: int = 1 if self.closest_monster is not None else 0

        deer_near: int = 1 if self.closest_deer is not None else 0

        at_right: int = 1 if self.x > self.map_width - 7 else 0
        at_left: int = 1 if self.x < 7 else 0
        at_top: int = 1 if self.y < 7 else 0
        at_bottom: int = 1 if self.y > self.map_height - 7 else 0

        low_energy: int = 1 if self.act_energy < self.max_energy // 2 else 0
        low_health: int = 1 if self.health < self.max_health // 2 else 0

        hunger_status: int = 1 if self.hunger > 50 else 0

        return (monster_near, deer_near, hunger_status, at_right, at_left,
                at_bottom, at_top, low_energy, low_health, self.target_dir,
                self.monster_dir, self.is_deer_in_range, self.can_attack,
                self.closest_unknown)

    # Events

    def _balance_hunger(self, dt: float) -> int:
        # Get health if not hungry
        if self.hunger < 100:
            if self.health < self.max_health:
                self.hunger += dt / 4
                self.health += dt
                self.health = min(self.health, self.max_health)
            else:
                self.hunger += dt / 8
        else:
            self.hunger = min(self.hunger, 100)
            self.health -= dt / 10

    def restart(self) -> None:
        self.alive = True
        self.health = self.max_health
        self.pos = pygame.Vector2(self.x, self.y)
        self.hunger = 0

        self.deer_attacks = 0
        self.ticks_lived = 0
        self.visited_cells = [0 for _ in range(
            self.map_grids * self.map_grids)]

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
        Acceleration : {self.acceleration}
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
        Is Deer in Range : {self.is_deer_in_range}
        ------------------
        Closest Unexplored : {self.closest_unknown}
        """

    def get_pos_draw(self) -> None:
        x, y = self.current_cell.get_pos()
        pos = y * 20 + x
        for i, val in enumerate(self.visited_cells):
            if i % 20 == 0:
                print()
            if pos == i:
                print(" () ", end="")
            else:
                print(f"{val:^4}", end="")
        print()

    def get_fitness(self) -> tuple[int, int]:
        """
        Function used to return fitness in order to
        optimize the rewards.
        """

        c_vis = sum(cell > 0 for cell in self.visited_cells)
        w_map = 5.0

        d_kill = self.deer_attacks
        w_food = 50.0

        t_surv = self.ticks_lived
        w_alive = 0.2

        w_still_alive = 0
        if self.alive:
            w_still_alive = 1000

        fitness = (c_vis * w_map) + (d_kill * w_food) + \
            (t_surv * w_alive) + w_still_alive

        return fitness, t_surv
