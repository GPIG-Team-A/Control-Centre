"""
Loads an environment from a file
"""

from environment import Environment, EnvType, get_environment_type_from_value
from constants import METERS_PER_TILE
from PIL import Image
from numpy import ceil


def image_to_environment(width: float, height: float, image_filename: str = "env.png")\
        -> Environment:
    """
    Contructs an Environment using an image

    :param width: The width of the environment in meters
    :param height: The height of the environment in meters
    :param image_filename: The name of the image file containing the environment information
    :return: The environment from the image
    """

    width_tiles = int(ceil(width / METERS_PER_TILE))
    height_tiles = int(ceil(height / METERS_PER_TILE))

    env = Environment(width_tiles, height_tiles)

    img = Image.open(image_filename, 'r')

    width_pixels_per_tile = int(ceil(img.size[0] / width_tiles))
    height_pixels_per_tile = int(ceil(img.size[1] / height_tiles))

    start = None
    end = None

    for y in range(height_tiles):
        if (y + 1) * height_pixels_per_tile > img.size[1]:
            continue

        for x in range(width_tiles):
            if (x + 1) * width_pixels_per_tile > img.size[0]:
                continue

            color_list = []
            size_list = []

            for pixel_y in range(height_pixels_per_tile):
                for pixel_x in range(width_pixels_per_tile):
                    coord_x = x * width_pixels_per_tile + pixel_x
                    coord_y = y * height_pixels_per_tile + pixel_y

                    color = img.getpixel((coord_x, coord_y))

                    if color not in color_list:
                        color_list.append(color)
                        size_list.append(1)

            chosen_color = EnvType.EMPTY.value

            if EnvType.OBSTACLE.value in color_list:
                chosen_color = EnvType.OBSTACLE.value
            elif EnvType.START.value in color_list and start is None:
                chosen_color = EnvType.START.value
                start = (x, y)
            elif EnvType.END.value in color_list and end is None:
                chosen_color = EnvType.END.value
                end = (x, y)

            env_type = get_environment_type_from_value(chosen_color)

            if env_type is not None:
                env.set_tile(x, y, env_type)

    env.set_start_end(start, end)

    return env
