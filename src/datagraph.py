import matplotlib.pyplot as plt
import pygame


class DataGraph:
    """
    Defines the characteristics of the graph instance.
    """

    def __init__(self, title: str, x_label: str, y_label: str, color: str) -> None:
        self.title: str = title
        self.xlabel: str = x_label
        self.ylabel: str = y_label

        self.x_points: list[float, ...] = []
        self.y_points: list[float, ...] = []

        self.n: int = 0
        self.sum_x: float = 0
        self.sum_y: float = 0
        self.sum_xy: float = 0
        self.sum_x2: float = 0

        self.color: str = color

        # Matplotlib config
        # ~ Lets code execution after showing the graph
        plt.ion()
        # ~ Deactivates interaction
        plt.rcParams['toolbar'] = 'None'

        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.line, = self.ax.plot([], [],
                                  color=self.color,
                                  linestyle='-',
                                  linewidth=2,
                                  marker='o',
                                  markersize=3,
                                  markerfacecolor='white',
                                  markeredgecolor='white'
                                  )
        self.avg_line, = self.ax.plot([], [],
                                      color='green',
                                      linestyle='--',
                                      label="Average Value"
                                      )

        self._config_axes()

    # Init config
    def _config_axes(self) -> None:
        self.ax.set_title(self.title, color="white")
        self.ax.set_xlabel(self.xlabel, color='white')
        self.ax.set_ylabel(self.ylabel, color='white')

        self.ax.tick_params(axis='x', labelcolor='white')
        self.ax.tick_params(axis='y', labelcolor='white')

        self.ax.grid(True, linestyle='--', alpha=0.5)

        self.ax.set_facecolor('#3b3a43')
        self.fig.set_facecolor('#2b2a33')

    # Update points
    def update(self, x_val: float, y_val: float) -> None:
        self.x_points.append(x_val)
        self.y_points.append(y_val)

        self.n += 1
        self.sum_x += x_val
        self.sum_y += y_val
        self.sum_xy += (x_val * y_val)
        self.sum_x2 += (x_val ** 2)

        self.line.set_data(self.x_points, self.y_points)

        if self.n > 1:
            slope_denominator = (self.n * self.sum_x2) - (self.sum_x ** 2)
            if slope_denominator != 0:
                slope = ((self.n * self.sum_xy) -
                         (self.sum_x * self.sum_y)) / slope_denominator
                # Point where it cross y axis
                y_intercept = (self.sum_y - (slope * self.sum_x)) / self.n

                x_start = self.x_points[0]
                x_end = self.x_points[-1]

                y_start = (slope * x_start) + y_intercept
                y_end = (slope * x_end) + y_intercept

                self.avg_line.set_data([x_start, x_end], [y_start, y_end])

        # Adjust perspective
        self.ax.relim()
        self.ax.autoscale_view()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    # Close the plot
    def close(self) -> None:
        plt.close("all")

    # Getters
    def get_title(self) -> str:
        return self.title
