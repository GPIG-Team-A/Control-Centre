"""
Global constants used within the decision centre project
"""

DISTANCE_BETWEEN_MOTORS: float = 0.11
""" The distance between the two motors in meters """

WHEEL_CIRCUMFERENCE: float = 0.276
""" The circumference of the wheel in meters """

TIME_BETWEEN_MOVEMENTS: float = 0.001
""" The time between each rover movement in seconds """

METERS_PER_TILE: float = 0.04
""" The size of the environment tiles in meters """

ROVER_STANDARD_DEVIATION: float = 0.8806615716635956 / 50.01724137931034
""" The normalised standard deviation of the real rover's individual motors """
