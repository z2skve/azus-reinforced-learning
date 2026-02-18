import matplotlib.pyplot as plt
import pygame


class DataGraph:
    """
    Defines the characteristics of the graph instance.
    """

    def __init__(self, title: str, x_label: str, y_label: str) -> None:
        self.title: str = title
        self.xlabel: str = x_label
        self.ylabel: str = y_label

        self.x_points: list[float, ...] = []
        self.y_points: list[float, ...] = []

        # Matplotlib config
        # ~ Lets code execution after showing the graph
        plt.ion()
        # ~ Deactivates interaction
        plt.rcParams['toolbar'] = 'None'

        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.line, = self.ax.plot([], [],
                                  color='#BF00FF',
                                  linestyle='-',
                                  linewidth=2,
                                  marker='o',
                                  markersize=3,
                                  markerfacecolor='white',
                                  markeredgecolor='white'
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

        self.line.set_data(self.x_points, self.y_points)

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
