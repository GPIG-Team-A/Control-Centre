"""
Handles the operations of the motor RPMs
"""

from digital_twin import constants


def get_time_for_distance(distance: float, motor_speeds: float) -> float:
    """
    Gets the time needed to traverse a distance at a specified speed

    :param distance: The distance to the goal in meters
    :param motor_speeds: The combined speeds of the motors in meters per second
    :return: The time needed to traverse the distance
    """
    return distance / motor_speeds


def get_motor_rpm(lin_speed: float) -> float:
    """
    Gets the motors speed if it is producing a forward linear speed x

    :param lin_speed: The forward linear speed from the motor
    :return: The rotation speed of the motor
    """
    return lin_speed * 60 / constants.WHEEL_CIRCUMFERENCE


def get_rover_speed(rpm: float) -> float:
    """
    Gets the linear wheel speed in the forward direction of the rover in meters per second

    :param rpm:
    :return: The linear velocity of the rover's wheel from its rpm in meters per second
    """
    return rpm * constants.WHEEL_CIRCUMFERENCE / 60


def angle_from_motor_speed(motor1_speed: float, motor2_speed: float,
                           time: float = constants.TIME_BETWEEN_MOVEMENTS) -> float:
    """
    Calculates the angle rotated by using two motors at the same speed in opposite directions.


    (IGNORES FRICTION) - MAYBE INCORRECT NEEDS TESTING

    θ = time * (motor1Speed + motor2Speed) / (2 * distanceToCentre)

    :param time: The time the motors are acting for at the current speeds
    :param motor1_speed: The linear speed of the first motor in m/s
    :param motor2_speed: The linear speed of the second motor in m/s
    :return: The angle rotated by in radians
    """
    return time * (motor1_speed - motor2_speed) / constants.DISTANCE_BETWEEN_MOTORS


def get_rpm_for_still_rotation(angle: float, time: float) -> float:
    """
    Returns the absolute motor RPMs needed to rotate the rover by the
    angle with no changes to its coordinates

    If:     x = getRPMForStillRotation(θ, t)

    Then:   θ = angleFromMotorSpeed(x, -x) * (t / T)

    Where:  T is the time between movements

    :param angle: The angle the rover wants to rotate
    :param time: The amount of time the rotation will occur
    :return: The absolute motor linear speeds need to rotate the angle
    """
    return angle * constants.DISTANCE_BETWEEN_MOTORS / (2 * time)
