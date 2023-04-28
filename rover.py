import rover_rpm_instructions
from CONSTANTS import DISTANCE_BETWEEN_MOTORS, TIME_BETWEEN_MOVEMENTS, METERS_PER_TILE
from maths_helper import convert_angle_to_2D_vector


class Rover:
    """
    The basic version of the rover's digital twin

    ...

    Attributes
    ----------

    _x : int
        The x coordinate of the rover within the environment

    _y : int
        The y coordinate of the rover within the environment

    _direction : float
        The angle (in radians) the rover is facing relative to the starting position
        This is the angle between the direction line and the x-axis

    ...

    Methods
    -------
    move(distance: float)
        Moves the rover the distance given

    rotate(dAngle: float)
        Rotates the rover given the change in angle

    getLocation() -> float
        Gets the coordinates of the rover in (x, y) format

    getDirection() -> float
        Gets the angular direction of the rover in radians

    getDirectionVector() -> tuple[float]:
        Gets the direction of the rover in its x and y components

    """

    def __init__(self, x: int = 0, y: int = 0, direction: float = 0):
        """
        :param x: The starting x position of the rover in meters
        :param y: The starting y position of the rover in meters
        :param direction: The starting angular direction of the rover in radians
        """
        self._x: int = x
        """ The x coordinate of the rover within the environment """
        self._y: int = y
        """ The y coordinate of the rover within the environment """

        self._direction: float = direction
        """ The angle (in radians) the rover is facing relative to the starting position. 
            This is the angle between the direction line and the x-axis
        """

    def motor_move(self, motor1_speed: float, motor2_speed: float, time:float = TIME_BETWEEN_MOVEMENTS):
        angle_change = rover_rpm_instructions.angleFromMotorSpeed(motor1_speed, motor2_speed)
        distance = (motor1_speed + motor2_speed) * time

        print(angle_change, distance)

        self.rotate(angle_change)
        self.move(distance)

    def rotate(self, angle: float):
        """
        Rotates the rover by a certain angle

        :param angle: The relative angle to rotate by, in radians
        """
        self._direction += angle

    def move(self, distance: float):
        """
        Moves the rover the given distance

        :param distance the rover will move
        """

        # Gets the direction unit vector
        dx, dy = convert_angle_to_2D_vector(self._direction)

        # Applies the direction with the distance to change the location
        self._x += distance * dx
        self._y += distance * dy

    def getLocation(self) -> tuple[float]:
        """
        :return: The rover's coordinates (x, y)
        """
        return self._x, self._y

    def getDirection(self) -> float:
        """
        :return: The angular direction of the rover in radians
        """
        return self._direction

    def getDirectionVector(self) -> tuple[float]:
        """
        :return: The direction of the rove as a 2D vector (dirX, dirY)
        """
        return convert_angle_to_2D_vector(self._direction)
