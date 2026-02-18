######################################################################
#                               main                                 #
######################################################################

import sys
from graphics import UI
import pygame
import random
import os

from azu import Azu
from deer import Deer
from monster import Monster

from agent import QLearningBrain

# Telemetry
from datagraph import DataGraph


def get_avrg_stat(azus: list[object, ...]) -> float:
    return sum(azu.get_reward() for azu in azus) / len(azus)


def main() -> None:
    # Initialize pygame
    pygame.init()
    clock = pygame.time.Clock()

    # Map config
    width: int = 1000
    height: int = 1000
    num_grids: int = 20

    # Verify dir existence
    path = "azus-brain"
    if not os.path.exists(path):
        os.makedirs(path)

    # Create UI
    ui: UI = UI("Azus Simulation", (43, 42, 51), width, height, num_grids)
    telemetry_mon: DataGraph = DataGraph(
        "Time Survived DataGraph", "Time (s)", "Ticks Survived")

    telemetry_mon.update(0, 0)

    # Control Variable
    running: bool = True

    # Entities Knowledge
    # -------------------------------------------------------------- #
    azu_master_brain = QLearningBrain(actions=[0, 1, 2, 3, 4, 5])
    azu_master_brain.load_from_disk(r"azus-brain/azu_knowledge.json")

    deer_master_brain = QLearningBrain(actions=[0, 1, 2, 3, 4])
    deer_master_brain.load_from_disk(r"azus-brain/deer_knowledge.json")

    monster_master_brain = QLearningBrain(actions=[0, 1, 2, 3, 4])
    monster_master_brain.load_from_disk(r"azus-brain/monster_knowledge.json")
    # -------------------------------------------------------------- #

    # Entities and Brains
    # ------------------------------------------------------------- #
    azus:     list[Azu, ...] = [
        Azu(f"{i}", random.randint(10, width - 10),
            random.randint(10, height - 10), (width, height), num_grids)
        for i in range(100)]

    for azu in azus:
        azu.brain = azu_master_brain

    deers:    list[Deer, ...] = [
        Deer(f"{i}", 200, 200, (1000, 1000), num_grids) for i in range(5)]

    for deer in deers:
        deer.brain = deer_master_brain

    monsters: list[Monster, ...] = [
        Monster(f"{i}", random.randint(10, width - 10),
                random.randint(10, height - 10), (width, height), num_grids)
        for i in range(1)]

    for monster in monsters:
        monster.brain = monster_master_brain

    entities: list[object, [...]] = [*azus, *deers, *monsters]
    # ------------------------------------------------------------- #

    # Start simulation
    try:
        # Saves last tick refresh
        last_graph_refresh: int = 0

        while running:
            dt = clock.tick(100) / 10
            ticks = pygame.time.get_ticks()

            # Get Stats
            avrg_reward = get_avrg_stat(azus)

            # Update Graphs
            if ticks - last_graph_refresh > 200 and False:  # Temporary
                telemetry_mon.update(ticks / 1000, avrg_reward)
                last_graph_refresh = ticks

            # Reduce Random Learning each Frame
            if azu_master_brain.epsilon > azu_master_brain.epsilon_min:
                azu_master_brain.epsilon *= 0.9999

            if deer_master_brain.epsilon > deer_master_brain.epsilon_min:
                deer_master_brain.epsilon *= 0.9999

            if monster_master_brain.epsilon > monster_master_brain.epsilon_min:
                monster_master_brain.epsilon *= 0.9999

            print(azu_master_brain.epsilon, deer_master_brain.epsilon)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            ui.clear()

            azus_alive = any(isinstance(obj, Azu) for obj in entities)
            deers_alive = any(isinstance(obj, Deer) for obj in entities)

            if not azus_alive:

                telemetry_mon.update(ticks / 1000, ticks - last_graph_refresh)
                last_graph_refresh = ticks

                entities: list[object, [...]] = [*azus, *deers, *monsters]
                for azu in azus:
                    azu.restart()

                for deer in deers:
                    deer.restart()

            if not deers_alive:
                entities: list[object, [...]] = [*azus, *deers, *monsters]
                for deer in deers:
                    deer.restart()

            # Update
            debug = 0
            for obj in entities:
                debug += 1
                obj.update(ui, dt, ui.screen)
                if debug == 1:
                    print(obj.get_info())

            # Clean entities
            entities = [obj for obj in entities if obj.alive]

            # Draw
            for obj in entities:
                obj.draw(ui.screen)

            ui.update_display()

    except Exception as e:
        print(e)
        exit(0)
    # End pygame
    finally:
        azu_master_brain.save_to_disk(r"azus-brain/azu_knowledge.json")
        deer_master_brain.save_to_disk(r"azus-brain/deer_knowledge.json")
        monster_master_brain.save_to_disk(r"azus-brain/monster_knowledge.json")

        telemetry_mon.close()
        pygame.quit()
        sys.exit()


# Initialize
if __name__ == "__main__":
    main()
