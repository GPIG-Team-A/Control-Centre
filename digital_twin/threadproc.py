"""
Thread that runs the actions of the commands sent to the digital rover
"""

import time
from threading import Thread
from digital_twin.rover_commands import RoverCommands
from digital_twin.rover import Rover
from digital_twin.constants import TIME_BETWEEN_MOVEMENTS


class RoverCommandThread(Thread):
    """
    Threaded class handling the updating of the rover's commands

    ...

    Attributes
    ----------

    _rover_commands: RoverCommands
        The command handler of the rover

    _rover: Rover
        The rover being updated

    """
    def __init__(self, rover: Rover):
        self._rover_commands: RoverCommands = RoverCommands()
        """ The command handler of the rover """
        self._rover = rover
        """ The rover being updated """
        Thread.__init__(self, daemon=True)

    def run(self) -> None:
        time.sleep(1)
        while True:
            # Updates the rover's commands
            self._rover_commands.update(self._rover)
            time.sleep(TIME_BETWEEN_MOVEMENTS)

    def get_rover_command(self) -> RoverCommands:
        """
        :return: The rover commands handler the thread is acting on
        """
        return self._rover_commands


# class UserCommandThread(Thread):
#     """
#     A thread that handle's the user's inputs to the simulation
#
#     ...
#
#     Attributes
#     ----------
#
#     _rover_command: RoverCommands
#         The handler of the rover's commands
#
#     """
#     def __init__(self, rover_command: RoverCommands):
#         self._rover_command: RoverCommands = rover_command
#         """ The handler of the rover's commands """
#
#         Thread.__init__(self, daemon=True)
#
#     def run(self) -> None:
#         time.sleep(1)
#         while True:
#             try:
#                 # Receives and forwards the given input to the rover's commands
#                 motor1_rpm, motor2_rpm, t = input("Enter Data > ").replace(" ", "").split(",")
#                 self._rover_command.add_command(float(motor1_rpm), float(motor2_rpm), float(t))
#             except ValueError:
#                 # If the inputs do not follow "motor1_rpm: float, motor2_rpm: float, time: float"
#                 print("VALUE ERROR")
