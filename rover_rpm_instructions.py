from CONSTANTS import DISTANCE_BETWEEN_MOTORS, TIME_BETWEEN_MOVEMENTS, WHEEL_CIRCUMFERENCE


def rpms_to_instructions(rpms: list[float]) -> list[tuple[float]]:
    pass


def get_time_for_distance(distance: float, motor_speeds: float) -> float:
    """
    Gets the time needed to traverse a distance at a specified speed

    :param distance: The distance to the goal in meters
    :param motor_speeds: The combined speeds of the motors in meters per second
    :return: The time needed to traverse the distance
    """
    return distance / motor_speeds


def getMotorRPM(linSpeed: float) -> float:
    """
    Gets the motors speed if it is producing a forward linear speed x

    :param linSpeed: The forward linear speed from the motor
    :return: The rotation speed of the motor
    """
    return linSpeed * 60 / WHEEL_CIRCUMFERENCE


def getRoverSpeed(rpm: float) -> float:
    """
    Gets the linear wheel speed in the forward direction of the rover in meters per second

    :param rpm:
    :return: The linear velocity of the rover's wheel from its rpm in meters per second
    """
    return rpm * WHEEL_CIRCUMFERENCE / 60


def angleFromMotorSpeed(motor1_speed: float, motor2_speed: float, time: float = TIME_BETWEEN_MOVEMENTS) -> float:
    """
    Calculates the angle rotated by using two motors at the same speed in opposite directions.


    (IGNORES FRICTION) - MAYBE INCORRECT NEEDS TESTING

    θ = time * (motor1Speed + motor2Speed) / (2 * distanceToCentre)

    :param time: The time the motors are acting for at the current speeds
    :param motor1_speed: The linear speed of the first motor in m/s
    :param motor2_speed: The linear speed of the second motor in m/s
    :return: The angle rotated by in radians
    """
    return time * (motor1_speed - motor2_speed) / DISTANCE_BETWEEN_MOTORS


def getRPMForStillRotation(angle: float, time: float) -> float:
    """
    Returns the absolute motor RPMs needed to rotate the rover by the angle with no changes to its coordinates

    If:     x = getRPMForStillRotation(θ, t)

    Then:   θ = angleFromMotorSpeed(x, -x) * (t / T)

    Where:  T is the time between movements

    :param angle: The angle the rover wants to rotate
    :param time: The amount of time the rotation will occur
    :return: The absolute RPMs needed for the rotation
    """
    return getMotorRPM(angle * DISTANCE_BETWEEN_MOTORS / (2 * time))
