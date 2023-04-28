from enum import Enum
from queue import Queue

import CONSTANTS
from rover import Rover
from maths_helper import get_angle_from_vectors, convert_angle_to_2D_vector
import numpy as np
import json


class RoverCommandType(Enum):
    MOVE = 0
    ROTATE = 1
    RPMS = 2


ROVER_TYPES: list[RoverCommandType] = [RoverCommandType.MOVE, RoverCommandType.ROTATE, RoverCommandType.RPMS]


class RoverCommands:
    """
    The rover command system that applies a series of commands to the rover

    The commands will be of the form (motor1_rpm, motor2_rpm, time)

    Motor1_rpm and motor2_rpm will be the rotation speeds of the rover's motors
    The time is how long the aforementioned motor speeds are applied for

    ...

    Attributes
    ----------

    _command_queue: Queue[tuple[float]]
        The data structure that contains the rover commands in order

    _current_command: tuple[float]
        The current command being applied to the rover, the time part will decrement at each step
        until there is no time remaining

    ...

    Methods
    -------

    add_command(command_type: RoverCommandType, value: float, time: float)
        Adds a command to the queue

    update(rover: rover)
        Handles the application of the commands to the rover

    _check_command()
        Checks whether the current command is still valid, and if not updates it

    """

    def __init__(self):
        self._command_queue: Queue[tuple[float]] = Queue()
        """ The data structure that contains the rover commands in order """

        self._current_command: tuple[float] = None
        """ The current command being applied to the rover """

    def add_command(self, command_type: RoverCommandType, value: float, time: float):
        """
        Adds a command to the queue

        :param command_type: The type of command being ran
        :param value: The value specific to the command type
        :param time: The time the command will run for
        """
        v = value

        if type(value) is not tuple:
            v = value * CONSTANTS.TIME_BETWEEN_MOVEMENTS / time

        self._command_queue.put((float(command_type.value), v, time))
        print(f"COMMAND ADDED: {(command_type, value, time)}")

    def update(self, rover: Rover):
        """
        Applies the commands to the rover

        :param rover: The rover the commands are run on
        """
        # Ensures the current command is current
        self._check_command()

        # Ensures there is a current command
        if self._current_command is not None:
            # Applies the current command
            commandType, value, timeUnitsLeft = self._current_command
            commandType = ROVER_TYPES[int(commandType)]

            if commandType == RoverCommandType.MOVE:
                rover.move(value)
            elif commandType == RoverCommandType.ROTATE:
                rover.rotate(value)
            elif commandType == RoverCommandType.RPMS:
                motor1_speed, motor2_speed = value
                rover.motor_move(motor1_speed, motor2_speed)

            # Updates the time remaining of the current command
            self._current_command = (commandType.value, value, timeUnitsLeft - CONSTANTS.TIME_BETWEEN_MOVEMENTS)

    def _check_command(self):
        """ Ensures that the current command is valid, updating if not """

        # Current command cannot be None, and the time remaining must not be above 0
        if self._current_command is None or self._current_command[2] <= 0:
            # Removes the current command
            self._current_command = None

            # Adds a new current command if the queue is not empty
            if not self._command_queue.empty():
                self._current_command = self._command_queue.get()

                value = self._current_command[1]
                if type(self._current_command[1]) is not tuple:
                    value = self._current_command[1] * self._current_command[2] / CONSTANTS.TIME_BETWEEN_MOVEMENTS

                    if ROVER_TYPES[int(self._current_command[0])] == RoverCommandType.ROTATE:
                        value *= 360 / (2 * np.pi)

                # Sends command information to the console
                print("COMMAND RUN:")
                print(f"Command Type: {ROVER_TYPES[int(self._current_command[0])].name}")
                print(f"Value       : {value}")
                print(f"TIME        : {int(self._current_command[2] * 1000) / 1000}s")


def save_rover_instructions_as_json(instructions: list[tuple[float]]):
    """
    Saves the rover's instruction as a json file

    :param instructions: The instructions to save
    """
    
    to_export = []
    for command_type, value, t in instructions:
        named_type = ""
        if command_type == RoverCommandType.MOVE:
            value = value * 100 # Convert to cm from m
            named_type = "MOVE"
        elif command_type == RoverCommandType.ROTATE:
            value = -360 * value / (2 * np.pi)
            named_type = "ROTATE"
        to_export.append({"type":named_type, "value":value})
    json.dump(to_export, open("test.json", "w"))


def create_rover_instructions_from_path(path: list[tuple[int]], rover_direction: float = 0) -> list[tuple[float]]:
    """
    Creates a set of rover instructions (command_type, value, time) from the path given

    :param path: The path of nodes the rover is to traverse
    :param rover_direction: The starting angular direction the rover is in, in radians
    :return: A list of rover instructions in the form (command_type, value, time)
    """
    cur_direction = rover_direction

    cur_pos = path[0]

    cmds: list[tuple[float]] = []

    for px, py in path[1:]:
        # Gets the direction to the next node
        dx = px - cur_pos[0]
        dy = py - cur_pos[1]

        # The current direction vector (dirX, dirY)
        v1 = convert_angle_to_2D_vector(cur_direction)
        # The next direction vector (dirX', dirY')
        v2 = (dx, dy)

        # The next angular direction of the rover
        new_angle = np.arctan2(dy, dx)

        # The angle the rover needs to turn to reach the new direction, is signed angular direction in radians
        dAngle = get_angle_from_vectors(v1, v2)

        # If the angle is 0 then no change in direction is needed
        if dAngle != 0:
            # Adds the change direction command
            cmds.append((RoverCommandType.ROTATE, -dAngle, 0.2))

        # Gets the distance that the rover will traverse in meters
        distance = np.sqrt(dx * dx + dy * dy) * CONSTANTS.METERS_PER_TILE

        # The maximum speed in m/s
        max_speed_rpm = 1

        # The time the rover will move at 'max_speed_rpm' to reach its next goal
        t = distance / max_speed_rpm

        # Adds the move forward command
        cmds.append((RoverCommandType.MOVE, distance, t))

        # Updates the rovers position and angle
        cur_pos = (px, py)
        cur_direction = new_angle

    return cmds