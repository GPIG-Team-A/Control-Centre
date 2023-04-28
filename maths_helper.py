import numpy as np


def convert_angle_to_2D_vector(angle: float) -> tuple[float]:
    """
    Converts an angle into a 2D vector (x, y)

    :param angle: The angle between the direction line and the x-axis
    :return: Direction vector (x, y)
    """
    x = np.cos(angle)
    y = np.sin(angle)

    # If either the x or y components are negligible, then they are set to 0 to avoid errors
    if abs(x) < 1e-10:
        x = 0

    if abs(y) < 1e-10:
        y = 0

    return x, y


def get_angle_from_vectors(v1: tuple[float], v2: tuple[float]) -> float:
    """
    Calculates the signed angle between the vectors given

    :param v1: The starting direction vector
    :param v2: The goal direction vector
    :return: The signed angular difference in radians
    """
    y = v1[0] * v2[1] - v1[1] * v2[0]
    x = v1[0] * v2[0] + v1[1] * v2[1]

    theta = -np.arctan2(y, x)

    # Ensures no unnecessary changes in direction for VERY small angles
    if abs(theta) <= 1e-5:
        theta = 0

    return theta
