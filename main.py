"""
The main file for the decision centre (mainly for testing purposes)
"""

import numpy

from digital_twin import constants
from digital_twin import environment
from digital_twin.rover import Rover
from digital_twin.threadproc import RoverCommandThread
from digital_twin.rover_commands import create_rover_instructions_from_path
from digital_twin.environment_interface import image_to_environment

if __name__ == '__main__':
    display = environment.setup_gui()

    env = image_to_environment(2.5, 2.5, image_filename="resources/test_env.png")

    # env = Environment(10, 40)
    # env.set_start_end((5, 39), None)

    start_pos, end_pos = env.get_start_end()

    rover = Rover((start_pos[0] + 0.5) * constants.METERS_PER_TILE,
                  (start_pos[1] + 0.5) * constants.METERS_PER_TILE, -numpy.pi / 2)
    env.set_rover(rover)

    cmd_thread = RoverCommandThread(rover)
    cmd_thread.start()

    rover_command = cmd_thread.get_rover_command()

    path = env.get_path()
    rover_cmds = create_rover_instructions_from_path(path, rover.get_direction())

    # tst = [(8, -8), (26, -26), (26, -25), (26, -25), (26, -25), (21, -20),
    # (21, -21), (27, -29), (26, -27), (25, -25), (25, -25), (24, -25), (22, -22),
    # (28, -32), (22, -21), (27, -26), (26, -27), (26, -27), (21, -21), (21, -21),
    # (28, -28), (27, -26), (25, -25), (24, -25), (21, -21), (27, -27), (26, -27),
    # (24, -24), (24, -24), (24, -25), (24, -25), (22, -22), (21, -21), (28, -26),
    # (27, -26), (25, -26), (24, -23), (23, -23), (25, -26), (23, -25), (24, -23),
    # (24, -25), (25, -25), (24, -23), (24, -24), (21, -20), (27, -25), (16, -15)]

    # mean_power = 50.01724137931034
    # stdev = 0.8806615716635956
    #
    # tst = [(mean_power + numpy.random.normal(0, stdev), -mean_power
    # + numpy.random.normal(0, stdev)) for _ in range(28)]
    #
    # max_speed = 1
    #
    # speeds = [(x[0] /100 * max_speed, -x[1] / 100 * max_speed) for x in tst]
    #
    # rover_cmds = [(RoverCommandType.RPMS, x, 0.1) for x in speeds]

    # save_rover_instructions_as_json(rover_cmds)

    for cmd_type, value, t in rover_cmds:
        rover_command.add_command(cmd_type, value, t)

    environment.run(display, env)
