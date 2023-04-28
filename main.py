"""
The main file for the decision centre (mainly for testing purposes)
"""

import numpy

from digital_twin import constants
from digital_twin import environment
from digital_twin.environment import Environment
from digital_twin.rover import Rover
from digital_twin.threadproc import RoverCommandThread
from digital_twin.rover_commands import create_rover_instructions_from_path
from digital_twin.environment_interface import image_to_environment


def create_rover_cmds(current_env: Environment):
    """
    Normal operation of the decision centre

    :param current_env: The environment being operated under
    """
    start_pos, _ = current_env.get_start_end()

    rover = Rover((start_pos[0] + 0.5) * constants.METERS_PER_TILE,
                  (start_pos[1] + 0.5) * constants.METERS_PER_TILE, -numpy.pi / 2)
    current_env.set_rover(rover)

    cmd_thread = RoverCommandThread(rover)
    cmd_thread.start()

    rover_command = cmd_thread.get_rover_command()

    path = current_env.get_path()
    rover_cmds = create_rover_instructions_from_path(path, rover.get_direction())

    for cmd_type, value, time in rover_cmds:
        rover_command.add_command(cmd_type, value, time)

    return rover_cmds


def simulate_environment(cur_env: Environment):
    """
    Simulates the environment to test whether the path is successful

    :param cur_env: The environment being operated under
    """
    start_pos, _ = cur_env.get_start_end()

    stdev = 0.8806615716635956 / 50.01724137931034

    cmd_thread = RoverCommandThread(None)
    cmd_thread.set_viewing_mode(False)
    cmd_thread.start()

    for x in range(2000):
        print(f"{numpy.round((x + 1) / 2000 * 100 * 10) / 10}% done")
        rover = Rover((start_pos[0] + 0.5) * constants.METERS_PER_TILE,
                      (start_pos[1] + 0.5) * constants.METERS_PER_TILE, -numpy.pi / 2,
                      motor_stdev=stdev)
        cur_env.set_rover(rover)
        cmd_thread.set_rover(rover)

        rover_command = cmd_thread.get_rover_command()

        path = cur_env.get_path()
        rover_cmds = create_rover_instructions_from_path(path, rover.get_direction())

        for cmd_type, value, time in rover_cmds:
            rover_command.add_command(cmd_type, value, time, False)


if __name__ == '__main__':
    display = environment.setup_gui()
    env = image_to_environment(2.5, 2.5, image_filename="resources/test_env.png")

    simulate_environment(env)
    environment.run(display, env)
