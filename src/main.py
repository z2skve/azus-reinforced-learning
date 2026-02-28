# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# MIT License
#
# Copyright (c) 2026 Marco Alcalde Campos
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

######################################################################
#                               main                                 #
######################################################################

import sys
import pygame
import random
import os
import traceback  # For error handling

from azu import Azu
from deer import Deer
from monster import Monster

from graphics import Ui
from agent import QLearningBrain
from datagraph import DataGraph
from optimizer import GeneticOptimizer

import time  # Debugging


def get_avrg_stat(azus: list[object, ...]) -> float:
    """
    Returns average stat from Azu class instances.
    """
    return sum(azu.get_reward() for azu in azus) / len(azus)


def check_dir_exist() -> None:
    """
    Checks if the entity's knowledge directory exists, if
    not creates it.
    """
    path = "azus-brain"
    if not os.path.exists(path):
        os.makedirs(path)


def get_entities(
        width: int, height: int, num_grids: int, genomes: dict) -> tuple:
    """
    Args:
        azu_master_brain: QLearningBrain -> Azu's hive mind
        deer_master_brain: QLearningBrain -> Deer's ...
        monster_master_brain: QLearningBrain -> Monster's ...

        width: int -> Map's horizontal resolution
        height: int -> Map's vertical resolution
        num_grids: int -> Number of map divisions

        genomes: dict -> Dictionary containing all configured rewards

    Returns:
        tuple(azus_list, deer_list, monster_list)
    """
    # Entities and Brains
    # ------------------------------------------------------------- #
    azus = []

    for i, g in enumerate(genomes):
        new_azu = Azu(
            name=f"Azu_{i}",
            x_pos=random.randint(10, width - 10),
            y_pos=random.randint(10, height - 10),
            map_dimension=(width, height),
            num_grids=num_grids,
            brain=QLearningBrain(actions=[0, 1, 2, 3, 4, 5]),
            genome=g
        )
        azus.append(new_azu)

    deers:    list[Deer, ...] = [
        Deer(
            name=f"Deer_{i}",
            x_pos=random.randint(10, width - 10),
            y_pos=random.randint(10, height - 10),
            map_dimension=(1000, 1000),
            num_grids=num_grids)
        for i in range(30)]

    for deer in deers:
        deer.brain = QLearningBrain(actions=[0, 1, 2, 3, 4])

    monsters: list[Monster, ...] = [
        Monster(f"{i}", random.randint(10, width - 10),
                random.randint(10, height - 10), (width, height), num_grids)
        for i in range(1)]

    for monster in monsters:
        monster.brain = QLearningBrain(actions=[0, 1, 2, 3, 4])

    return azus, deers, monsters
    # ------------------------------------------------------------- #


def main() -> None:
    # Initialize pygame
    clock = pygame.time.Clock()

    # Map config
    width: int = 1000
    height: int = 1000
    num_grids: int = 20

    # Create UI
    ui: Ui = Ui("Azus Simulation", (43, 42, 51), width, height, num_grids)

    # Verify needed dirs
    check_dir_exist()

    # Telemetry
    ticks_mon: DataGraph = DataGraph(
        "Ticks Survived DataGraph", "Generations", "Ticks Survived", '#BF00FF')

    hunted_deer_mon: DataGraph = DataGraph(
        "Deers Hunted DataGraph", "Generations", "Deers Hunted", '#279FF5')

    # Genetic Algorithm vars
    # ----------------------------------------------- #
    POP_SIZE: int = 20
    STEPS_PER_GEN: int = 75_000

    optimizer = GeneticOptimizer(pop_size=POP_SIZE)

    # ~ Initial number of generations
    saved_pop, start_gen = optimizer.load_checkpoint()

    if saved_pop:
        populat_genomes = saved_pop
        gen_number = start_gen
    else:
        populat_genomes = optimizer.create_init_gen()
        gen_number = 0
    # ----------------------------------------------- #

    # Bellman's algorithm > 0 and < 1
    W_EPSILON: float = 0.999

    # UI Constants
    # ~ Defines how many generations should happen
    # ~ before showing the results
    RENDER_EVERY: int = 500

    # Create entities list
    azus, deers, monsters = get_entities(width, height, num_grids,
                                         populat_genomes)

    entities: list[object, [...]] = [*azus, *deers, *monsters]
    # ------------------------------------------------------------- #

    # Start simulation
    try:
        # Saves last tick refresh
        last_graph_refresh: int = 0

        # Control Variable
        running: bool = True

        # Azu stat
        hunted_deer: int = 0

        # Sets drawing on or off
        visual: bool = False

        # Framerate
        framerate: int = 0  # ~ Default
        frame_speed: int = 10  # x100 times

        # Init steps num
        steps: int = 0

        while running:
            # tiempo_act = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            dt = clock.tick(framerate)
            if framerate != 0:
                dt = dt / frame_speed

            if not (0 < W_EPSILON < 1):
                raise ValueError("W_EPSILON must be between 0 and 1")

            # Reduce Random Learning each Frame
            for azu in azus:
                if azu.brain.epsilon > azu.brain.epsilon_min:
                    azu.brain.epsilon *= W_EPSILON

            for deer in deers:
                if deer.brain.epsilon > deer.brain.epsilon_min:
                    deer.brain.epsilon *= W_EPSILON

            for monster in monsters:
                if monster.brain.epsilon > monster.brain.epsilon_min:
                    monster.brain.epsilon *= W_EPSILON

            azus_alive = any(isinstance(obj, Azu) for obj in entities)
            deers_alive = sum(isinstance(obj, Deer) for obj in entities)

            # var1 = (time.time() - tiempo_act)
            # tiempo_act = time.time()

            if steps - last_graph_refresh >= STEPS_PER_GEN or not azus_alive:

                if gen_number % RENDER_EVERY == 0:
                    visual = True
                    framerate = 100
                    ui.set_visual(True)
                else:
                    visual = False
                    framerate = 0
                    ui.set_visual(False)

                gen_number += 1

                attmpt_num = (gen_number % 3)

                if attmpt_num == 1:
                    rated_genomes = []

                    for azu in azus:
                        azu.brain.epsilon = 1

                    for deer in deers:
                        deer.brain.epsilon = 1

                    for monster in monsters:
                        monster.brain.epsilon = 1

                azus_times = []
                for i, azu in enumerate(azus):
                    score, azu_time = azu.get_fitness()
                    if attmpt_num == 1:

                        rated_genomes.append([score, azu.genome])
                    else:
                        rated_genomes[i][0] += score
                    azus_times.append(azu_time)
                    azu.restart()

                for deer in deers:
                    deer.restart()

                entities: list[object, [...]] = [*azus, *deers, *monsters]

                if attmpt_num == 0:
                    populat_genomes = optimizer.evolve(rated_genomes)

                    for i, azu in enumerate(azus):
                        azu.genome = populat_genomes[i]

                    optimizer.save_checkpoint(populat_genomes, gen_number)

                # XXX: DEBUG
                best_time = max(azus_times)
                print(f"Best Time Gen {gen_number}: {best_time}\n")

                # Print for debugging
                # print(azu_master_brain.epsilon)

                # Telemetry
                ticks_mon.update(gen_number, best_time)
                hunted_deer_mon.update(gen_number, hunted_deer)

                last_graph_refresh = steps
                hunted_deer = 0

            # var2 = (time.time() - tiempo_act)
            # tiempo_act = time.time()

            if deers_alive <= 29:
                hunted_deer += 1
                print("Deer hunted in this generation :", hunted_deer)
                entities: list[object, [...]] = [*azus, *deers, *monsters]
                for deer in deers:
                    if not deer.alive:
                        deer.restart()

            # var3 = (time.time() - tiempo_act)
            # tiempo_act = time.time()
            # Debugging var
            debug = 0

            # Update
            for obj in entities:
                debug += 1
                obj.update(ui, dt)

                # Only for debugging
                if debug == -1:  # Off for now
                    print(obj.get_info())

            # var4 = (time.time() - tiempo_act)
            # tiempo_act = time.time()

            # Clear dead entities
            entities = [obj for obj in entities if obj.alive]

            # Draw
            if visual:
                ui.clear()

                for obj in entities:
                    obj.draw(ui.screen)

                ui.update_display()

            steps += 1

            # var5 = (time.time() - tiempo_act)

            # print(var1, var2, var3, var4, var5)
            # tiempo_act = time.time()

    except Exception:
        traceback.print_exc()
        exit(0)
    # End pygame
    finally:
        # Telemetry
        hunted_deer_mon.close()
        ticks_mon.close()

        pygame.quit()
        sys.exit()


# Initialize
if __name__ == "__main__":
    main()
