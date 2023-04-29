"""
Handles the environment the rover will operate in
"""

import enum

import numpy as np
import pygame
from pygame.locals import QUIT

from digital_twin.rover import Rover
from digital_twin.constants import METERS_PER_TILE, DISTANCE_BETWEEN_MOTORS

SCREEN_WIDTH = 1000
""" The width of the GUI in pixels"""
SCREEN_HEIGHT = 900
""" The height of the GUI in pixels """

TILE_START_X = 10
""" The starting x coordinate of the tile map """
TILE_START_Y = 10
""" The starting y coordinate of the tile map """
TILE_WIDTH = 20
""" The width of each tile in pixels """
TILE_HEIGHT = 20
""" The height of each tile in pixels """


class EnvType(enum.Enum):
    """ A user-friendly description of the contents of the environment


        Each Environment Type has a colour associated with it, which is the colour of the
        tile being drawn
    """

    EMPTY = (128, 128, 128)
    """ An empty space in the environment that is transversable by the rover. GREY """
    OBSTACLE = (255, 0, 0)
    """ An occupied space in the environment that the rover cannot transverse through. RED """
    EXPLORED = (255, 165, 0)
    """ A space in the environment that the rover has already explored. ORANGE """
    START = (255, 255, 0)
    """ The starting position of the rover. YELLOW """
    END = (0, 255, 0)
    """ The goal position of the rover. GREEN"""


def get_environment_type_from_value(value: tuple[int]) -> EnvType:
    """
    :param value: The value (colour) of the EnvType enum
    :return: The environment type corresponding to the value given
    """
    for env_type in EnvType:
        if env_type.value == value:
            return env_type

    return None


class Environment:
    """
    The basic simulation of the environment the rover is expected to navigate through

    ...

    Attributes
    ----------

    _map: list[list[EnvType]]
        A 2D list representing the simple top-down view of the environment

    _rover: Rover
        The rover acting within the environment

    _start: tuple[int]
        The starting position of the rover

    _end: tuple[int]
        The goal position of the rover

    _path: list[tuple[int]]
        The cached path of nodes the rover can traverse

    ...

    Methods
    -------

    set_start_end(start: tuple[int], end: tuple[int])
        Sets the starting and goal positions of the rover within the environment

    set_tile(x: int, y: int, eType: EnvType)
        Sets a tile within the map to be a certain environment type

    get_tile(x: int, y: int) -> EnvType
        Gets the type of the tile at the coordinates given

    size() -> tuple[int]
        Returns the size of the environment in the form (width, height)

    randomly_assign_obstacles(perc: float = 0.2)
        Randomly creates obstacles within the environment with the amount being a percentage of
        the total nodes

    get_path() -> list[tuple[int]]
        Gets the path from the start to the end, that the rover can traverse without encountering
        an obstacle

    """

    def __init__(self, width: int, height: int):
        """
        :param width: The amount of tiles in each row of the 2D map
        :param height: The amount of tiles in each column of the 2D map
        """

        self._map: list[list[EnvType]] = [[EnvType.EMPTY for _ in range(width)]
                                          for _ in range(height)]
        """ The 2D representation of the environment from a top-down view 
            Each tile is accessed using its coordinates (x, y) by self._map[y][x]
        """

        self._rover: Rover = None
        """ The rover acting within the environment """

        self._start: tuple[int] = None
        """ The starting node, which the rover will begin at """
        self._end: tuple[int] = None
        """ The goal node, which the rover will work towards """

        self._path = None
        """ The cache list of coordinates which the rover can traverse from the start 
            to end without encountering any obstacles
        """

    def set_start_end(self, start: tuple[int], end: tuple[int]):
        """
        Sets the starting and goal positions for the rover within the environment

        :param start: The starting node (x, y)
        :param end: The goal node (x, y)
        """
        self._start = start
        self._end = end

        self.set_tile(start[0], start[1], EnvType.START)

        if end is not None:
            self.set_tile(end[0], end[1], EnvType.END)

    def set_rover(self, rover: Rover):
        """
        Sets the rover that will interact with the environment

        :param rover: The rover of the environment
        """
        self._rover = rover

    def get_rover(self) -> Rover:
        """
        :return: The active rover in the environment
        """
        return self._rover

    def set_tile(self, x: int, y: int, env_type: EnvType):
        """
        Sets the type of the tile within the environment at the coordinates given

        :param x: The x coordinate of the tile
        :param y: The y coordinate of the tile
        :param env_type: The environment type the tile should be
        """
        self._map[y][x] = env_type

    def get_tile(self, x: int, y: int):
        """
        Gets the type of the tile at the coordinates given

        :param x: The x coordinate of the tile
        :param y: The y coordinate of the tile
        :return: The environment type of the tile at the coordinate (x, y)
        """
        return self._map[y][x]

    def size(self):
        """
        :return: The size of the environment's map in the form (width, height)
        """
        return len(self._map[0]), len(self._map)

    def get_start_end(self) -> tuple[tuple[int], tuple[int]]:
        """
        :return: The start and end coordinates of course in the format
                 (startX, startY), (endX, endY)
        """
        return self._start, self._end

    def randomly_assign_obstacles(self, perc: float = 0.2):
        """
        Randomly assigns a percentage of the nodes within the environment to be obstacles
        TESTING FUNCTION

        :param perc: The decimal percentage of the total nodes to be obstacles
        """
        assigned = 0

        map_size = self.size()[0] * self.size()[1]

        while assigned < perc * map_size:
            abs_pos = np.random.randint(0, map_size)

            pos = (abs_pos % self.size()[0], abs_pos // self.size()[0])

            # Only empty tiles can change to obstacles
            if self.get_tile(pos[0], pos[1]) == EnvType.EMPTY:
                self.set_tile(pos[0], pos[1], EnvType.OBSTACLE)
                assigned += 1

    def get_path(self) -> list[tuple[int]]:
        """
        :return: The path between the start and end nodes that can be reached
        without traversing any obstacles
        """

        # No path between null starts and ends
        if self._start is None or self._end is None:
            return []

        # If there is no cached path then a new path is created using Theta*
        if self._path is None:
            self._path = pathfind(self, self._start, self._end)

        # Returns the cached path
        return self._path


def _cost(traversal_costs: list[list[float]], point_1: tuple[int], point_2: tuple[int]) \
        -> float:
    """
    Gets the traversal cost between 2 nodes

    :param traversal_costs: The traversal cost between all nodes and the starting node
    :param point_1: The current node
    :param point_2: The node being traversed to from n1
    :return: The cost of the traversal from n1 to n2
    """
    # The traversal cost between the starting node and n1
    g_val = traversal_costs[point_1[1]][point_1[0]]

    dx = point_2[0] - point_1[0]
    dy = point_2[1] - point_1[1]

    distance_heuristic = np.sqrt(dx * dx + dy * dy)

    # Angular heuristic
    ang = np.abs(np.arctan(dy / dx)) if dx != 0 else np.pi / 2

    return g_val + ang + distance_heuristic


def _poll(open_nodes_queue: list[tuple[int]], traversal_costs: list[list[float]],
          end_pos: tuple[int]) -> tuple[int]:
    """
    Polls a node from the queue given the lowest cost to the goal node

    :param open_nodes_queue: The open nodes being explored
    :param traversal_costs: The traversal cost between all nodes and the starting node
    :param end_pos: The goal node of the search algorithm
    :return: The next node to be explored
    """
    min_cst = float("inf")
    out_pos = None

    for pos in open_nodes_queue:
        cst = _cost(traversal_costs, pos, end_pos)

        if cst < min_cst:
            min_cst = cst
            out_pos = pos

    open_nodes_queue.remove(out_pos)

    return out_pos


def f_x(point_1, point_2, y):
    """
    :param point_1: (x, y) coordinate
    :param point_2: (x, y) coordinate
    :param y: y coordinate that lies on the line between points 1 and 2
    :return: Given a line between points 1 and 2, returns the x coordinate corresponding
             to the y on the given line
    """
    gradient = (point_2[0] - point_1[0]) / (point_2[1] - point_1[1])

    return gradient * (y - point_1[1]) + point_1[0]


def f_y(point_1, point_2, x):
    """
    :param point_1: (x, y) coordinate
    :param point_2: (x, y) coordinate
    :param x: x coordinate that lies on the line between points 1 and 2
    :return: Given a line between points 1 and 2, returns the y coordinate corresponding
             to the x on the given line
    """
    gradient = (point_2[1] - point_1[1]) / (point_2[0] - point_1[0])

    return gradient * (x - point_1[0]) + point_1[1]


def get_intersected_coordinates(point_1: tuple[float], point_2: tuple[float]) \
        -> list[tuple[int]]:
    """
    :param point_1: (x, y) coordinate
    :param point_2: (x, y) coordinate
    :return: The coordinates of the tiles that intersect between the line between point_1 and
             point_2
    """

    x_min = int(np.floor(np.min([point_1[0], point_2[0]])))
    x_max = int(np.floor(np.max([point_1[0], point_2[0]])))

    y_min = int(np.floor(np.min([point_1[1], point_2[1]])))
    y_max = int(np.floor(np.max([point_1[1], point_2[1]])))

    return [(x, int(f_y(point_1, point_2, x))) for x in range(x_min, x_max)] \
           + [(int(f_x(point_1, point_2, y)), y) for y in range(y_min, y_max)]


def _is_line_of_sight(env: Environment, point_1: tuple[int], point_2: tuple[int]) -> bool:
    dir_vector = [point_2[0] - point_1[0], point_2[1] - point_1[1]]
    magnitude = np.sqrt(dir_vector[0] * dir_vector[0] + dir_vector[1] * dir_vector[1])

    dir_vector[0] = dir_vector[0] / magnitude
    dir_vector[1] = dir_vector[1] / magnitude

    dist = DISTANCE_BETWEEN_MOTORS / METERS_PER_TILE

    perpendicular_vector = [dir_vector[1], -dir_vector[0]]

    rays_cast = 3

    start_point = [point_1[0] + 0.5 - (dist / 2) * perpendicular_vector[0],
                   point_1[1] + 0.5 - (dist / 2) * perpendicular_vector[1]]

    end_point = [point_2[0] + 0.5 - (dist / 2) * perpendicular_vector[0],
                 point_2[1] + 0.5 - (dist / 2) * perpendicular_vector[1]]

    for ray in range(rays_cast):
        start_point = (start_point[0] + ray * (dist / (rays_cast - 1)) * perpendicular_vector[0],
                       start_point[1] + ray * (dist / (rays_cast - 1)) * perpendicular_vector[1])

        end_point = (end_point[0] + ray * (dist / (rays_cast - 1)) * perpendicular_vector[0],
                     end_point[1] + ray * (dist / (rays_cast - 1)) * perpendicular_vector[1])

        for x, y in get_intersected_coordinates(start_point, end_point):
            try:
                if env.get_tile(x, y) == EnvType.OBSTACLE:
                    return False
            except IndexError:
                pass

    return True


def _is_line_of_sight_legacy(env: Environment, point_1: tuple[int], point_2: tuple[int]) -> bool:
    """
    Checks whether 2 nodes can traverse to each other without encountering an obstacle

    :param env: The environment being traversed
    :param point_1: Node 1
    :param point_2: Node 2
    :return: True if there is a line of sight between the nodes, False otherwise
    """

    # Simple ray tracing
    dir_vector = [point_2[0] - point_1[0], point_2[1] - point_1[1]]
    scale_factor = np.sqrt(dir_vector[0] * dir_vector[0] + dir_vector[1] * dir_vector[1]) * 100

    dir_vector[0] = dir_vector[0] / scale_factor
    dir_vector[1] = dir_vector[1] / scale_factor

    dist = DISTANCE_BETWEEN_MOTORS / METERS_PER_TILE

    perpendicular_vector = [dir_vector[1], -dir_vector[0]]
    p_v_magnitude = np.sqrt(perpendicular_vector[0] * perpendicular_vector[0]
                            + perpendicular_vector[1] * perpendicular_vector[1])
    perpendicular_vector[0] /= p_v_magnitude
    perpendicular_vector[1] /= p_v_magnitude

    rays_cast = 3

    # Gets the first point of the line perpendicular to the rover's direction at
    # which the rays will be cast
    # EXAMPLE BELOW ( point marked as X )
    #
    #         , - ~ ~ ~ -/,
    #     , '           /   ' ,
    #   ,              /        ,
    #  ,              /          ,
    # ,              /            ,
    # ,             /             ,
    # ,            /              ,
    #  ,          /              ,
    #   ,        /              ,
    #     ,     /            , '
    #       ' -X, _ _ _ ,  '

    start_point = [point_1[0] + 0.5 - (dist / 2) * perpendicular_vector[0],
                  point_1[1] + 0.5 - (dist / 2) * perpendicular_vector[1]]

    # Sends rays that checks if any of the nodes between the two nodes given are obstacles
    for ray in range(rays_cast):
        for scale_val in range(int(scale_factor)):
            point_x = start_point[0] + ray * (dist / (rays_cast - 1)) * perpendicular_vector[0]

            point_y = start_point[1] + ray * (dist / (rays_cast - 1)) * perpendicular_vector[1]

            pos_x = point_x + dir_vector[0] * scale_val
            pos_y = point_y + dir_vector[1] * scale_val

            try:
                if env.get_tile(int(pos_x), int(pos_y)) == EnvType.OBSTACLE:
                    return False
            except IndexError:
                pass
    return True


def _update_vertex(env: Environment, open_nodes_queue: list[tuple[int]],
                   traversal_costs: list[list[float]], parent: list[list[tuple[int]]],
                   point_1: tuple[int], point_2: tuple[int]):
    """
    Updates the node's traversal cost and parent node

    :param env: The environment being traversed
    :param open_nodes_queue: The open list of nodes being explored
    :param traversal_costs: The traversal cost between all nodes and the starting node
    :param parent: The parent matrix of every node
    :param point_1: Node 1
    :param point_2: Node 2
    """
    # Gets the parent of node 1
    n_parent = parent[point_1[1]][point_1[0]]

    if _is_line_of_sight(env, point_1, point_2):
        if _is_line_of_sight(env, n_parent, point_2):
            # If there's a line of sight between n1's parent and n2

            # If the cost of the traversal from n1's parent and n2 is smaller
            # than n2's current traversal cost then n2's parent is set to n1's parent
            if _cost(traversal_costs, n_parent, point_2) < traversal_costs[point_2[1]][point_2[0]]:
                traversal_costs[point_2[1]][point_2[0]] = _cost(traversal_costs, n_parent, point_2)
                parent[point_2[1]][point_2[0]] = n_parent

                if point_2 not in open_nodes_queue:
                    open_nodes_queue.append(point_2)
        # If the cost of the traversal from n1 to n2 is smaller than n2's
        # current traversal cost then n2's parent is set to n1
        elif _cost(traversal_costs, point_1, point_2) < traversal_costs[point_2[1]][point_2[0]]:
            traversal_costs[point_2[1]][point_2[0]] = _cost(traversal_costs, point_1, point_2)
            parent[point_2[1]][point_2[0]] = point_1

            if point_2 not in open_nodes_queue:
                open_nodes_queue.append(point_2)


def _get_neighbours(env: Environment, node: tuple[int]) -> list[tuple[int]]:
    """
    Gets the adjacent, non-obstacle, nodes to the node given

    :param env: The environment being traversed
    :param node: The node in question
    :return: The list of the node's neighbouring nodes
    """

    adj = [
        (1, 0),
        (0, -1),
        (-1, 0),
        (0, 1)
    ]

    x, y = node

    neighbours = []

    for dx, dy in adj:
        new_x = x + dx
        new_y = y + dy

        # Ensures the neighbour is in the map
        if new_x < 0 or new_x >= env.size()[0]:
            continue
        if new_y < 0 or new_y >= env.size()[1]:
            continue

        # Ensures the neighbour isn't an obstacle
        if env.get_tile(new_x, new_y) == EnvType.OBSTACLE:
            continue

        neighbours.append((new_x, new_y))

    return neighbours


def pathfind(environment: Environment, start: tuple[int], end: tuple[int]) -> list[tuple[int]]:
    """
    Finds a path between the 2 points given

    :param environment: The environment the nodes are in
    :param start: The node where the path will begin
    :param end: The node where the path will end
    :return: A list of the nodes from the start to end
    """
    print(f"PATH FINDING BETWEEN {start} and {end}")

    env_width, env_height = environment.size()

    traversal_costs: list[list[float]] = [[float("inf") for _ in range(env_width)]
                                          for _ in range(env_height)]
    parent: list[list[tuple[float]]] = [[None for _ in range(env_width)] for _ in range(env_height)]

    traversal_costs[start[1]][start[0]] = 0
    parent[start[1]][start[0]] = start

    open_nodes_queue: list[tuple[int]] = []
    close_nodes_list: list[tuple[int]] = []

    open_nodes_queue.append(start)

    while len(open_nodes_queue) > 0:
        node = _poll(open_nodes_queue, traversal_costs, end)

        if node is None:
            continue

        if node == end:
            print("PATH FOUND")
            break

        print(f"EXPLORE {node}")

        # DEBUGGING ONLY
        # environment.set_tile(node[0], node[1], EnvType.EXPLORED)

        close_nodes_list.append(node)

        neighbours = _get_neighbours(environment, node)

        for neighbour in neighbours:
            if neighbour not in close_nodes_list:
                _update_vertex(environment, open_nodes_queue, traversal_costs,
                               parent, node, neighbour)

    reverse_path = []

    node = end
    reverse_path.append(node)

    while node != start:
        node = parent[node[1]][node[0]]
        reverse_path.append(node)

    path = [reverse_path[x] for x in range(len(reverse_path) - 1, -1, -1)]

    print("PATH FINDING COMPLETE")

    return path


def setup_gui() -> pygame.Surface:
    """
    Sets up the environment GUI

    :return: The environment GUI
    """

    pygame.init()

    return pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def run(display: pygame.surface, environment: Environment):
    """
    Runs the environment GUI's loop

    :param display: The environment GUI
    :param environment: The environment being displayed
    """

    # Runs until the GUI is closed
    is_running = True
    while is_running:
        # Updates the environment onto the GUI
        update(display, environment)

        # Updates any changes the GUI to the display
        pygame.display.update()

        # Checks if the user closes the GUI
        # If so, then the GUI and its related processes are terminated
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                is_running = False


