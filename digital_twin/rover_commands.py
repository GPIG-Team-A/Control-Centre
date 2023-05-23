"""
Handles the commands the rover will receive
"""


from enum import Enum
from queue import Queue
from typing import Any

import numpy as np
from digital_twin import constants
from digital_twin.rover import Rover
from digital_twin.maths_helper import get_angle_from_vectors, convert_angle_to_2d_vector
from digital_twin.environment import Environment


class RoverCommandType(Enum):
    """
    The type of the commands
    """

    MOVE = 0
    """ Command for the rover to move a certain distance """
    ROTATE = 1
    """ Command for the rover to rotate a certain angle """
    RPMS = 2
    """ Command to run certain speeds on the motors for a certain time """
    SET_POSITION = 3
    """ Command to set the position of the rover """
    SET_ANGLE = 4
    """ Command to mine """
    MINE = 5
    """ 
    Command to set the angle of the rover 
    MUST BE SET AS SINGLE ELEMENT TUPLE
    """


ROVER_TYPES: list[RoverCommandType] = [RoverCommandType.MOVE,
                                       RoverCommandType.ROTATE,
                                       RoverCommandType.RPMS,
                                       RoverCommandType.SET_POSITION,
                                       RoverCommandType.SET_ANGLE,
                                       RoverCommandType.MINE]


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

    def is_empty(self) -> bool:
        """
        :return: True if the command queue is empty
        """
        return self._command_queue.empty() and self._current_command is None

    def add_command(self, command_type: RoverCommandType,
                    value: float, time: float, is_printing: bool = True):
        """
        Adds a command to the queue

        :param command_type: The type of command being ran
        :param value: The value specific to the command type
        :param time: The time the command will run for
        :param is_printing: If true the current command is printed to the console
        """
        val = value

        if not isinstance(value, tuple) and command_type != RoverCommandType.ROTATE:
            val = value * constants.TIME_BETWEEN_MOVEMENTS / time

        self._command_queue.put((float(command_type.value), val, time))

        if is_printing:
            print(f"COMMAND ADDED: {(command_type, value, time)}")

    def update(self, rover: Rover, is_printing: bool = True):
        """
        Applies the commands to the rover

        :param is_printing: If true the current command is printed to the console
        :param rover: The rover the commands are run on
        """
        # Ensures the current command is current
        self._check_command(is_printing)

        # Ensures there is a current command
        if self._current_command is not None:
            # Applies the current command
            command_type, value, time_units_left = self._current_command
            command_type = ROVER_TYPES[int(command_type)]

            if isinstance(value, float):
                if np.isnan(value):
                    self._current_command = None
                    return

            if command_type == RoverCommandType.MOVE:
                rover.move(value)
            elif command_type == RoverCommandType.ROTATE:
                rover.set_angle(value)
            elif command_type == RoverCommandType.RPMS:
                motor1_speed, motor2_speed = value
                rover.motor_move(motor1_speed, motor2_speed)
            elif command_type == RoverCommandType.SET_POSITION:
                rover.set_position(value)
            elif command_type == RoverCommandType.SET_ANGLE:
                rover.set_angle(value[0])

            # Updates the time remaining of the current command
            self._current_command = (command_type.value, value, time_units_left -
                                     constants.TIME_BETWEEN_MOVEMENTS)

    def _check_command(self, is_printing: bool = True):
        """
        Ensures that the current command is valid, updating if not

        :param is_printing: If true the current command is printed to the console
        """

        # Current command cannot be None, and the time remaining must not be above 0
        if self._current_command is None or self._current_command[2] <= 0:
            # Removes the current command
            self._current_command = None

            # Adds a new current command if the queue is not empty
            if not self._command_queue.empty():
                self._current_command = self._command_queue.get()

                value = self._current_command[1]
                if not isinstance(self._current_command[1], tuple):
                    value = self._current_command[1] * self._current_command[2]\
                            / constants.TIME_BETWEEN_MOVEMENTS

                    if ROVER_TYPES[int(self._current_command[0])] == RoverCommandType.ROTATE:
                        value *= 360 / (2 * np.pi)

                if is_printing:
                    # Sends command information to the console
                    print("COMMAND RUN:")
                    print(f"Command Type: {ROVER_TYPES[int(self._current_command[0])].name}")
                    print(f"Value       : {value}")
                    print(f"TIME        : {int(self._current_command[2] * 1000) / 1000}s")


def rover_instructions_to_json(instructions: list[tuple[float]]):
    """
    Saves the rover's instruction as a json file

    :param instructions: The instructions to save
    """

    to_export = []
    for command_type, value, _ in instructions:
        named_type = ""
        if command_type == RoverCommandType.MOVE:
            value = value * 100 # Convert to cm from m
            named_type = "MOVE"
        elif command_type == RoverCommandType.ROTATE:
            value = 360 * (value + np.pi / 2) / (2 * np.pi)
            named_type = "ROTATE"
        elif command_type == RoverCommandType.MINE:
            value = 0
            named_type = "MINE"
        to_export.append({"type":named_type, "value":value})

    print(to_export)
    return to_export


def create_rover_instructions_from_logs(env: Environment, log_obj: list[dict[str, Any]]):
    """
    Creates the rover's instructions from the logs provided

    Parameters
    ----------
    env
    log_obj

    Returns
    -------

    """
    cmds = []

    start_pos = env.get_start_end()[0]

    start_pos = ((start_pos[0] + 0.5) * constants.METERS_PER_TILE,
                 (start_pos[1] + 0.5) * constants.METERS_PER_TILE)

    last_end_rotation = env.get_start_end_directions()[0]

    cmds.append((RoverCommandType.SET_POSITION, start_pos, 0.1))
    cmds.append((RoverCommandType.SET_ANGLE, (last_end_rotation,), 0.1))

    angle_adj = None

    for log_dict in log_obj:
        if len(log_dict) == 0:
            continue

        start_rotation = log_dict["Starting Yaw"] * np.pi / 180
        end_rotation = log_dict["Ending Yaw"] * np.pi / 180

        if angle_adj is None:
            angle_adj = last_end_rotation - start_rotation

        start_rotation += angle_adj
        end_rotation += angle_adj

        rotation_angle = start_rotation - last_end_rotation

        if rotation_angle > np.pi:
            rotation_angle -= np.pi * 2

        if rotation_angle < -np.pi:
            rotation_angle += np.pi * 2

        cmds.append((RoverCommandType.ROTATE, rotation_angle, 0.2))

        last_end_rotation = end_rotation

        motor_powers = log_dict["Power Values"]

        for motor1_power, motor2_power in motor_powers:
            motor1_power = motor1_power / 100 * constants.POWER_TO_SPEED_CONVERSION
            motor2_power = -motor2_power / 100 * constants.POWER_TO_SPEED_CONVERSION

            cmds.append((RoverCommandType.RPMS, (motor1_power, motor2_power), 0.1))

    return cmds


def create_rover_instructions_from_path(env: Environment,
                                        path: list[tuple[int]],
                                        rover_direction: float = 0,
                                        rover_final_direction: float = 0)\
        -> list[tuple[float]]:
    """
    Creates a set of rover instructions (command_type, value, time) from the path given

    :param path: The path of nodes the rover is to traverse
    :param rover_direction: The starting angular direction the rover is in, in radians
    :return: A list of rover instructions in the form (command_type, value, time)
    """
    cur_direction = rover_direction

    cur_pos = path[0]

    cmds: list[tuple[float]] = []

    end_pos = env.get_start_end()[1]


    for path_x, path_y in path[1:]:
        # Gets the direction to the next node
        dx = path_x - cur_pos[0]
        dy = path_y - cur_pos[1]

        # The current direction vector (dirX, dirY)
        vector_1 = convert_angle_to_2d_vector(cur_direction)
        # The next direction vector (dirX', dirY')
        vector_2 = (dx, dy)

        # The next angular direction of the rover
        new_angle = np.arctan2(dy, dx)

        # The angle the rover needs to turn to reach the new direction,
        # is signed angular direction in radians
        d_angle = get_angle_from_vectors(vector_1, vector_2)

        # If the angle is 0 then no change in direction is needed
        if d_angle != 0:
            if new_angle > np.pi:
                new_angle -= np.pi * 2

            if new_angle < -np.pi:
                new_angle += np.pi * 2

            # Adds the change direction command
            cmds.append((RoverCommandType.ROTATE, new_angle, 0.2))

        # Gets the distance that the rover will traverse in meters
        distance = np.sqrt(dx * dx + dy * dy) * constants.METERS_PER_TILE

        print(dx, dy, distance)

        # The time the rover will move at 'max_speed_rpm' to reach its next goal
        time = distance / constants.ROVER_MAX_SPEED

        # Adds the move forward command
        cmds.append((RoverCommandType.MOVE, distance, time))

        # Check for mining
        if (path_x, path_y) in end_pos:
            angle = -np.pi / 2
            if end_pos.index((path_x, path_y)) == len(end_pos) - 1:
                angle = np.pi / 2
            cmds.append((RoverCommandType.ROTATE, angle, 0.2))
            cmds.append((RoverCommandType.MINE, 0, 0.1))
            cmds.append((RoverCommandType.ROTATE, new_angle, 0.2))

        # Updates the rovers position and angle
        cur_pos = (path_x, path_y)
        cur_direction = new_angle

    # The current direction vector (dirX, dirY)
    vector_1 = convert_angle_to_2d_vector(cur_direction)
    # The next direction vector (dirX', dirY')
    vector_2 = convert_angle_to_2d_vector(rover_final_direction)

    # The angle the rover needs to turn to reach the new direction,
    # is signed angular direction in radians
    d_angle = get_angle_from_vectors(vector_1, vector_2)

    # If the angle is 0 then no change in direction is needed
    if d_angle != 0:
        # Adds the change direction command
        cmds.append((RoverCommandType.ROTATE, -d_angle, 0.2))

    return cmds
