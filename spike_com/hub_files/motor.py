"""
    Represents a Motor connected to a SpikeHub

    Information of the CLI API can be found by using
    help(hub.port.A.motor) (switch A for whatever port has motor attached)
"""
import time
import hub
from log import log

class Motor:
    """
        Represents a Motor connected to a SpikeHub

        Attributes:
            rotation (int): Current rotation in degrees (0-360)
            FORWARD (int): Enum for forward direction
            BACKWARD (int): Enum for backward direction
    """
    FORWARD = 1 # Motor moving 'forward'
    BACKWARD = -1 # Motor moving 'backward'

    def __init__(self, port, inverted=False):
        """
            Create a Motor connected to the specified port

            Args:
                port (str): A, B, C, D, E, or F
                inverted (boolean): Whether the motor runs inverted (i.e. forwards is backwards) (default False)
        """
        self.port = port
        self.rotation = 0 # Unknown right now
        assert self.port in ['A', 'B', 'C', 'D', 'E', 'F']
        self.inverted = inverted
        self._motor = getattr(hub.port, port).motor
        self._motor.mode([(1,0), (2,2), (3,1), (0,0)])
    
    def start(self, speed=100, direction=FORWARD):
        """
            Begin the motor at the given speed and direction

            Args:
                speed (int): Speed of the motor as a percentage 0-100 (default: 100)
                direction (int): Direction of the motor, either motor.FORWARD, motor.BACKWARD
        """
        if self.inverted:
            direction = -1 * direction
        self._motor.run_at_speed(speed * direction)
    
    def run_to_position(self, degrees, speed=100, blocking=False):
        """
        
        """
        self._motor.run_to_position(degrees, speed=speed)
    
    def run_for_degrees(self, degrees, speed=100, blocking=False):
        """
            Run the motor for the given number of degrees

            There's an issue that hub.port.X.motor.run_for_degrees on the Micropython CLI
                doesn't keep the rotation to within 360deg.
            This will need to be fixed in the future.
        """
        if self.inverted:
            speed = -speed
        self._motor.run_for_degrees(degrees, speed=speed)
    
    def get_rotation(self):
        """
            Return current rotation of motor
        """
        return self._motor.get()[1]
    
    def get_current_power(self):
        """
            TODO: Investigate this more, not sure if it's power or speed
        """
        return self._motor.get()[3]

    def get_current_pwm(self):
        return self._motor.get()[0]

    def is_running(self):
        """
            Return whether the motor is running
        """
        current_power = self.get_current_power()
        return current_power == None or current_power > 0
    
    def wait_until_finished(self):
        """
            Wait until this motor has finished moving
        """
        while self.is_running():
            time.sleep(0.1)

    def stop(self, blocking=False):
        """
            Stop the motor
        """
        self._motor.brake()