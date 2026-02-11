######################################################################
#                               main                                 #
######################################################################

import sys
from graphics import UI
import pygame
import random

from azu import Azu
from deer import Deer
from monster import Monster

from agent import QLearningBrain


def main():
    # Initialize pygame
    pygame.init()
    clock = pygame.time.Clock()

    width: int = 1000
    height: int = 1000

    # Create UI
    ui: UI = UI("Azus Simulation", (43, 42, 51), width, height)

    # Control Variable
    running: bool = True

    # Entities Knowledge
    azu_master_brain = QLearningBrain(actions=[0, 1, 2, 3, 4])
    azu_master_brain.load_from_disk(r"azus-brain/azu_knowledge.json")

    deer_master_brain = QLearningBrain(actions=[0, 1, 2, 3, 4])
    deer_master_brain.load_from_disk(r"azus-brain/deer_knowledge.json")

    monster_master_brain = QLearningBrain(actions=[0, 1, 2, 3, 4])
    monster_master_brain.load_from_disk(r"azus-brain/monster_knowledge.json")

    # Entities and Brains
    # ------------------------------------------------------------- #
    azus:     list[Azu, ...] = [
        Azu(f"{i}", random.randint(10, width - 10), random.randint(10, height - 10), (width, height)) for i in range(100)]

    for azu in azus:
        azu.brain = azu_master_brain

    deers:    list[Deer, ...] = [
        Deer(f"{i}", 200, 200, (1000, 1000)) for i in range(5)]

    for deer in deers:
        deer.brain = deer_master_brain

    monsters: list[Monster, ...] = [
        Monster(f"{i}", random.randint(10, width - 10), random.randint(10, height - 10), (width, height)) for i in range(5)]

    for monster in monsters:
        monster.brain = monster_master_brain

    entities: list[object, [...]] = [*azus, *deers, *monsters]
    # ------------------------------------------------------------- #
    #
    # Start simulation
    while running:
        dt = clock.tick(60) / 20
        print("PT", dt)

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

    # End pygame
    azu_master_brain.save_to_disk(r"azus-brain/azu_knowledge.json")
    deer_master_brain.save_to_disk(r"azus-brain/deer_knowledge.json")
    monster_master_brain.save_to_disk(r"azus-brain/monster_knowledge.json")
    pygame.quit()
    sys.exit()


# Initialize
if __name__ == "__main__":
    main()
