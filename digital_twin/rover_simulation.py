"""
Handles the simulation of the rover in order to improve the path finding
"""


import numpy as np
from digital_twin.environment import Environment, EnvType
from digital_twin.rover_commands import create_rover_instructions_from_path, RoverCommands
from digital_twin.constants import DISTANCE_BETWEEN_MOTORS,\
    ROVER_STANDARD_DEVIATION, METERS_PER_TILE
from digital_twin.rover import Rover


def normal(mean: float, stdev: float, x: int):
    """
    :param mean: The mean of the distribution
    :param stdev: The standard deviation of the distribution
    :param x: The random result
    :return: P(X = x), where X ~ N(mean, stdev ** 2)
    """
    return (1 / (stdev * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / stdev) ** 2)


def binomial_approx(trial_num: int, probability: float, x: int):
    """
    Uses the normal distribution to approximate P(X = x), where X ~ B(trial_num, probability)

    :param trial_num: The amount of trials
    :param probability: The probability of a single trial's success
    :param x: The amount of trials that have succeeded
    :return: P(X = x)
    """
    return normal(trial_num * probability, np.sqrt(trial_num * probability * (1 - probability)), x)


def binomial_cdf(trial_num: int, probability: float, x: int):
    """
    :param trial_num: The amount of trials
    :param probability: The probability of a single trial's success
    :param x: The cumulative amount of successful trials
    :return: P(X < x), where X ~ B(trial_num, probability)
    """
    return np.sum([binomial_approx(trial_num, probability, i) for i in range(x)])


def get_critical_value(trial_num, probability, significance_value) -> int:
    """
    :param trial_num: The amount of trials
    :param probability: The proposed probability of a single trial's success
    :param significance_value: The maximum probability required to suggest an
                               amount of trials provides evidence that the real
                               probability of success is lower than the proposed
    :return: The value of x such that x = max v (P(X < v) <= s)
             where X ~ B(trial_num, significance_value)
    """
    cur_p = 0
    cur_x = -1

    while cur_p < significance_value:
        cur_x += 1
        cur_p = binomial_cdf(trial_num, probability, cur_x)

    return cur_x


def is_valid_position(env: Environment, x: float, y: float):
    """
    :param env: The environment the coordinates are in
    :param x: The x component of the coordinate within env
    :param y: The y component of the coordinate within env
    :return: True if (x, y) is in the bounds of the environment, and is not an obstacle
    """
    width, height = env.size()

    cur_x = int(x / METERS_PER_TILE)
    cur_y = int(y / METERS_PER_TILE)

    is_in_bounds = True

    if cur_x < 0 or cur_x > width:
        is_in_bounds = False

    if cur_y < 0 or cur_y > height:
        is_in_bounds = False

    has_passed = is_in_bounds

    if has_passed:
        try:
            has_passed = env.get_tile(cur_x, cur_y) != EnvType.OBSTACLE
        except IndexError:
            has_passed = False

    return has_passed


def simulate(env: Environment, trial_number: int, prob_failure: float,
             significance_value: float = 0.05):
    """
    Simulates a number of trials to result in a path that the
    rover will have a specified probability of failure using hypothesis testing

    :param env: The environment the path is in
    :param trial_number: The amount of trials that the hypothesis testing will use
    :param prob_failure: The maximum probability of failure the user wants for the rover
    :param significance_value: The significance value for the hypothesis tests
    :return: A path that fulfills the maximum probability of failure, if this cannot
             be done, then an empty list is returned
    """
    print("START SIMULATION")

    adjustment_value = 0.01

    # Calculate critical value
    critical_value = get_critical_value(trial_number, prob_failure, significance_value)

    if critical_value == -1:
        raise ValueError("INVALID CRITICAL VALUE")

    cur_width_val = DISTANCE_BETWEEN_MOTORS

    env_start_x, env_start_y = env.get_start_end()[0]

    direction = -np.pi/2

    # Run simulations until optimal path is found, or no path can be found
    while True:
        print(f"ATTEMPTING WIDTH {cur_width_val}")

        # Find a path
        env.reset_path()
        path = env.get_path(cur_width_val)

        if len(path) == 0:
            print("FAILED")
            break
        
        print(path)

        rover_cmds = create_rover_instructions_from_path(env.get_start_end(), path, direction)

        failed_trials = 0

        # Run `trial_num` amount of trials
        for i in range(trial_number):
            print(f"\rTrial {i}", end="")

            cur_rover = Rover((env_start_x + 0.5) * METERS_PER_TILE,
                              (env_start_y + 0.5) * METERS_PER_TILE,
                              env.get_start_end_directions()[0],
                              motor_stdev=ROVER_STANDARD_DEVIATION)
            rover_command = RoverCommands()

            env.set_rover(cur_rover)

            for cmd in rover_cmds:
                rover_command.add_command(cmd[0], cmd[1], cmd[2], is_printing=False)

            while not rover_command.is_empty():
                rover_command.update(cur_rover, False)

                cur_x, cur_y = cur_rover.get_location()

                has_passed = is_valid_position(env, cur_x, cur_y) and\
                    is_valid_position(env, cur_x - DISTANCE_BETWEEN_MOTORS / 2,
                                      cur_y - DISTANCE_BETWEEN_MOTORS / 2) and\
                    is_valid_position(env, cur_x + DISTANCE_BETWEEN_MOTORS / 2,
                                      cur_y - DISTANCE_BETWEEN_MOTORS / 2) and\
                    is_valid_position(env, cur_x - DISTANCE_BETWEEN_MOTORS / 2,
                                      cur_y + DISTANCE_BETWEEN_MOTORS / 2) and\
                    is_valid_position(env, cur_x + DISTANCE_BETWEEN_MOTORS / 2,
                                      cur_y + DISTANCE_BETWEEN_MOTORS / 2)

                if not has_passed:
                    failed_trials += 1
                    break

            if failed_trials >= critical_value:
                break

        print(f"\nFailed {failed_trials} out of {critical_value - 1} allowed failures on trial {i}")

        # If failed the hypothesis adjust the path finding
        # If passed end the session
        if failed_trials < critical_value:
            break

        cur_width_val += adjustment_value

    return path
