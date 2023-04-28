import enum

import numpy as np
import pygame
from pygame.locals import *

from rover import Rover
from CONSTANTS import METERS_PER_TILE, DISTANCE_BETWEEN_MOTORS

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
        Gets the path from the start to the end, that the rover can traverse without encountering an obstacle

    """

    def __init__(self, width: int, height: int):
        """
        :param width: The amount of tiles in each row of the 2D map
        :param height: The amount of tiles in each column of the 2D map
        """

        self._map: list[list[EnvType]] = [[EnvType.EMPTY for _ in range(width)] for _ in range(height)]
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
        """ The cache list of coordinates which the rover can traverse from the start to end without encountering
            any obstacles
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

    def set_tile(self, x: int, y: int, eType: EnvType):
        """
        Sets the type of the tile within the environment at the coordinates given

        :param x: The x coordinate of the tile
        :param y: The y coordinate of the tile
        :param eType: The environment type the tile should be
        """
        self._map[y][x] = eType

    def get_tile(self, x, y):
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
        :return: The path between the start and end nodes that can be reached without traversing any obstacles
        """

        # No path between null starts and ends
        if self._start is None or self._end is None:
            return []

        # If there is no cached path then a new path is created using Theta*
        if self._path is None:
            self._path = pathfind(self, self._start, self._end)

        # Returns the cached path
        return self._path


def _cost(g: list[list[float]], n1: tuple[int], n2: tuple[int]) -> float:
    """
    Gets the traversal cost between 2 nodes

    :param g: The traversal cost between all nodes and the starting node
    :param n1: The current node
    :param n2: The node being traversed to from n1
    :return: The cost of the traversal from n1 to n2
    """
    # The traversal cost between the starting node and n1
    g_val = g[n1[1]][n1[0]]

    dx = n2[0] - n1[0]
    dy = n2[1] - n1[1]

    # Distance heuristic
    h = np.sqrt(dx * dx + dy * dy)

    # Angular heuristic
    ang = np.abs(np.arctan(dy / dx)) if dx != 0 else np.pi / 2

    return g_val + ang + h


def _poll(OPEN: list[tuple[int]], g: list[list[float]], end_pos: tuple[int]) -> tuple[int]:
    """
    Polls a node from the queue given the lowest cost to the goal node

    :param OPEN: The open nodes being explored
    :param g: The traversal cost between all nodes and the starting node
    :param end_pos: The goal node of the search algorithm
    :return: The next node to be explored
    """
    min_cst = float("inf")
    out_pos = None

    for pos in OPEN:
        cst = _cost(g, pos, end_pos)

        if cst < min_cst:
            min_cst = cst
            out_pos = pos

    OPEN.remove(out_pos)

    return out_pos


def f_x(p1, p2, y):
    m = (p2[0] - p1[0]) / (p2[1] - p1[1])

    return m * (y - p1[1]) + p1[0]

def f_y(p1, p2, x):
    m = (p2[1] - p1[1]) / (p2[0] - p1[0])

    return m * (x - p1[0]) + p1[1]


def get_intersected_coordinates(p1: tuple[float], p2: tuple[float]) -> list[tuple[int]]:
    x_min = int(np.floor(np.min([p1[0], p2[0]])))
    x_max = int(np.floor(np.max([p1[0], p2[0]])))

    y_min = int(np.floor(np.min([p1[1], p2[1]])))
    y_max = int(np.floor(np.max([p1[1], p2[1]])))

    return [(x, int(f_y(p1, p2, x))) for x in range(x_min, x_max)] \
        + [(int(f_x(p1, p2, y)), y) for y in range(y_min, y_max)]


def _is_line_of_sight(env: Environment, n1: tuple[int], n2: tuple[int]) -> bool:
    dir_vector = [n2[0] - n1[0], n2[1] - n1[1]]
    magnitude = np.sqrt(dir_vector[0] * dir_vector[0] + dir_vector[1] * dir_vector[1])

    dir_vector[0] = dir_vector[0] / magnitude
    dir_vector[1] = dir_vector[1] / magnitude

    dist = DISTANCE_BETWEEN_MOTORS / METERS_PER_TILE

    perpendicular_vector = [dir_vector[1], -dir_vector[0]]

    rays_cast = 3

    startPoint = [n1[0] + 0.5 - (dist / 2) * perpendicular_vector[0],
                  n1[1] + 0.5 - (dist / 2) * perpendicular_vector[1]]

    endPoint = [n2[0] + 0.5 - (dist / 2) * perpendicular_vector[0],
                  n2[1] + 0.5 - (dist / 2) * perpendicular_vector[1]]

    for n in range(rays_cast):
        p1 = (startPoint[0] + n * (dist / (rays_cast - 1)) * perpendicular_vector[0],
              startPoint[1] + n * (dist / (rays_cast - 1)) * perpendicular_vector[1])

        p2 = (endPoint[0] + n * (dist / (rays_cast - 1)) * perpendicular_vector[0],
              endPoint[1] + n * (dist / (rays_cast - 1)) * perpendicular_vector[1])

        for x, y in get_intersected_coordinates(p1, p2):
            try:
                if env.get_tile(x, y) == EnvType.OBSTACLE:
                    return False
            except IndexError:
                pass

    return True


def _is_line_of_sight_legacy(env: Environment, n1: tuple[int], n2: tuple[int]) -> bool:
    """
    Checks whether 2 nodes can traverse to each other without encountering an obstacle

    :param env: The environment being traversed
    :param n1: Node 1
    :param n2: Node 2
    :return: True if there is a line of sight between the nodes, False otherwise
    """

    # Simple ray tracing
    dir_vector = [n2[0] - n1[0], n2[1] - n1[1]]
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

    startPoint = [n1[0] + 0.5 - (dist / 2) * perpendicular_vector[0],
                  n1[1] + 0.5 - (dist / 2) * perpendicular_vector[1]]

    # Sends rays that checks if any of the nodes between the two nodes given are obstacles
    for n in range(rays_cast):
        for i in range(int(scale_factor)):
            pointX = startPoint[0] + n * (dist / (rays_cast - 1)) * perpendicular_vector[0]

            pointY = startPoint[1] + n * (dist / (rays_cast - 1)) * perpendicular_vector[1]

            posX = pointX + dir_vector[0] * i
            posY = pointY + dir_vector[1] * i

            try:
                if env.get_tile(int(posX), int(posY)) == EnvType.OBSTACLE:
                    return False
            except:
                pass
    return True


def _update_vertex(env: Environment, OPEN: list[tuple[int]], g: list[list[float]],
                   parent: list[list[tuple[int]]], n1: tuple[int], n2: tuple[int]):
    """
    Updates the node's traversal cost and parent node

    :param env: The environment being traversed
    :param OPEN: The open list of nodes being explored
    :param g: The traversal cost between all nodes and the starting node
    :param parent: The parent matrix of every node
    :param n1: Node 1
    :param n2: Node 2
    """
    # Gets the parent of node 1
    n_parent = parent[n1[1]][n1[0]]

    if _is_line_of_sight(env, n1, n2):
        if _is_line_of_sight(env, n_parent, n2):
            # If there's a line of sight between n1's parent and n2

            # If the cost of the traversal from n1's parent and n2 is smaller
            # than n2's current traversal cost then n2's parent is set to n1's parent
            if _cost(g, n_parent, n2) < g[n2[1]][n2[0]]:
                g[n2[1]][n2[0]] = _cost(g, n_parent, n2)
                parent[n2[1]][n2[0]] = n_parent

                if not (n2 in OPEN):
                    OPEN.append(n2)
        else:
            # If the cost of the traversal from n1 to n2 is smaller than n2's
            # current traversal cost then n2's parent is set to n1
            if _cost(g, n1, n2) < g[n2[1]][n2[0]]:
                g[n2[1]][n2[0]] = _cost(g, n1, n2)
                parent[n2[1]][n2[0]] = n1

                if not (n2 in OPEN):
                    OPEN.append(n2)


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
        newX = x + dx
        newY = y + dy

        # Ensures the neighbour is in the map
        if newX < 0 or newX >= env.size()[0]:
            continue
        if newY < 0 or newY >= env.size()[1]:
            continue

        # Ensures the neighbour isn't an obstacle
        if env.get_tile(newX, newY) == EnvType.OBSTACLE:
            continue

        neighbours.append((newX, newY))

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

    g: list[list[float]] = [[float("inf") for _ in range(env_width)] for _ in range(env_height)]
    parent: list[list[tuple[float]]] = [[None for _ in range(env_width)] for _ in range(env_height)]

    g[start[1]][start[0]] = 0
    parent[start[1]][start[0]] = start

    OPEN: list[tuple[int]] = []
    CLOSED: list[tuple[int]] = []

    OPEN.append(start)

    while len(OPEN) > 0:
        node = _poll(OPEN, g, end)

        if node is None:
            continue

        if node == end:
            print("PATH FOUND")
            break

        print(f"EXPLORE {node}")

        # DEBUGGING ONLY
        # environment.set_tile(node[0], node[1], EnvType.EXPLORED)

        CLOSED.append(node)

        neighbours = _get_neighbours(environment, node)

        for n in neighbours:
            if not (n in CLOSED):
                _update_vertex(environment, OPEN, g, parent, node, n)

    revPath = []

    node = end
    revPath.append(node)

    while node != start:
        node = parent[node[1]][node[0]]
        revPath.append(node)

    path = [revPath[x] for x in range(len(revPath) - 1, -1, -1)]

    print("PATH FINDING COMPLETE")

    return path


def setupGUI() -> pygame.Surface:
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
    isRunning = True
    while isRunning:
        # Updates the environment onto the GUI
        update(display, environment)

        # Updates any changes the GUI to the display
        pygame.display.update()

        # Checks if the user closes the GUI
        # If so, then the GUI and its related processes are terminated
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                isRunning = False


def update(display: pygame.surface, environment: Environment):
    """
    Updates the environment onto the GUI

    :param display: The environment GUI
    :param environment: The environment being simulated
    """
    # Clears the display
    display.fill((50, 50, 50))

    width, height = environment.size()

    # Iterates through each tile
    for y in range(height):
        for x in range(width):
            # Gets the tile's position in the GUI
            posX = TILE_START_X + x * (TILE_WIDTH + 2)
            posY = TILE_START_Y + y * (TILE_HEIGHT + 2)

            # Gets the type of the tile, this has a colour corresponding to it
            tileType = environment.get_tile(x, y)

            if tileType is None:
                tileType = EnvType.EMPTY

            # Draws the tile
            pygame.draw.rect(display, tileType.value, (posX, posY, TILE_WIDTH, TILE_HEIGHT))

    path = environment.get_path()

    for i in range(len(path) - 1):
        pos_1 = path[i]
        pos_2 = path[i + 1]

        pygame.draw.line(display, (0, 0, 0),
                         (TILE_START_X + (pos_1[0] + 0.5) * (TILE_WIDTH + 2),
                          TILE_START_Y + (pos_1[1] + 0.5) * (TILE_HEIGHT + 2)),
                         (TILE_START_X + (pos_2[0] + 0.5) * (TILE_WIDTH + 2),
                          TILE_START_Y + (pos_2[1] + 0.5) * (TILE_HEIGHT + 2)), width=2)

    # Handles the displaying of the rover
    rover = environment.get_rover()

    if rover is not None:
        rX, rY = rover.getLocation()

        # Converts the rover's coordinates from meters to pixels
        rX *= (TILE_WIDTH + 2) / METERS_PER_TILE
        rY *= (TILE_HEIGHT + 2) / METERS_PER_TILE

        rover_diameter = DISTANCE_BETWEEN_MOTORS * TILE_WIDTH / METERS_PER_TILE

        # Adjusts the coordinates so that they fit in the map
        roverX = rX + TILE_START_X - rover_diameter / 2
        roverY = rY + TILE_START_Y - rover_diameter / 2

        rover_sprite = pygame.image.load("Rover.png")
        rover_sprite = pygame.transform.rotozoom(rover_sprite, -rover.getDirection() * 360 / (2 * np.pi) - 90,
                                                 rover_diameter / 16)

        display.blit(rover_sprite, (roverX, roverY))
