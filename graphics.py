######################################################################
#                             graphics                               #
######################################################################

import pygame


class Cell:
    def __init__(self, x_pos: int, y_pos: int) -> None:
        self.x: int = x_pos
        self.y: int = y_pos
        self.pos = (self.x, self.y)

        self.entities: set = set()

    def add_entity(self, obj: object) -> None:
        self.entities.add(obj)

    def rm_entity(self, obj: object) -> None:
        self.entities.discard(obj)

    def get_pos(self) -> None:
        return self.pos


class UI:
    def __init__(self, title: str, bg_color: tuple[int, int, int], width: int = 1000, height: int = 1000) -> None:
        pygame.init()
        self.bg_color: tuple[int, int, int] = bg_color
        self.width: int = width
        self.height: int = height
        self.num_grids: int = 20

        self.title: str = title

        self._set_window_size()
        self._calc_grid_pixel_size()
        self._create_cells()
        self._set_title()

    def clear(self) -> None:
        self.screen.fill(self.bg_color)

    def update_display(self) -> None:
        pygame.display.flip()

    def grid_division(self, num_grids: int) -> None:
        self.num_grids = num_grids
        self._calc_grid_pixel_size()

    def get_cells(self) -> tuple[Cell, ...]:
        return self.cells

    def _set_title(self) -> None:
        pygame.display.set_caption(self.title)

    def _set_window_size(self) -> None:
        self.screen: pygame.Surface = pygame.display.set_mode(
            (self.width, self.height))

    def _calc_grid_pixel_size(self):
        self.grid_size_x: int = self.width // self.num_grids
        self.grid_size_y: int = self.height // self.num_grids

    def _create_cells(self) -> None:
        self.cells: tuple[Cell, ...] = tuple(
            Cell(x_pos, y_pos)
            for y_pos in range(self.num_grids)
            for x_pos in range(self.num_grids)
        )

    # Methods called by instances
    def get_cell_at_pos(self, pos: pygame.Vector2) -> Cell:
        grid_x: int = int(pos.x / self.grid_size_x)
        grid_y: int = int(pos.y / self.grid_size_y)

        grid_x = max(0, min(grid_x, self.num_grids - 1))
        grid_y = max(0, min(grid_y, self.num_grids - 1))

        return self.cells[(grid_y * self.num_grids) + grid_x]

    def get_neighbors(self, obj: object, cell: tuple, radius: int):
        x, y = cell.get_pos()
        neighbors = set()

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy

                if 0 <= nx < self.num_grids and 0 <= ny < self.num_grids:
                    index = ny * self.num_grids + nx
                    target_cell = self.cells[index]
                    neighbors.update(target_cell.entities)

        neighbors.discard(obj)
        return neighbors
