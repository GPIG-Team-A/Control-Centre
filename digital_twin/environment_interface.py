"""
Loads an environment from a file
"""

from PIL import Image
from numpy import ceil
from digital_twin.environment import Environment, EnvType, get_environment_type_from_value
from digital_twin.constants import METERS_PER_TILE


def image_to_environment(width: float, height: float, image_filename: str = "resources/env.png") \
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

    env = Environment(width_tiles + 2, height_tiles + 2)

    img = Image.open(image_filename, 'r')

    width_pixels_per_tile = int(ceil(img.size[0] / (width_tiles - 2)))
    height_pixels_per_tile = int(ceil(img.size[1] / (height_tiles - 2)))

    start = None
    end = []

    for y in range(1, height_tiles - 1):
        for x in range(1, width_tiles - 1):
            if (x + 1) * width_pixels_per_tile > img.size[0] \
                    or (y + 1) * height_pixels_per_tile > img.size[1]:
                continue

            color_list = []
            size_list = []

            for pixel_y in range(height_pixels_per_tile):
                for pixel_x in range(width_pixels_per_tile):
                    coord_x = x * width_pixels_per_tile + pixel_x
                    coord_y = y * height_pixels_per_tile + pixel_y

                    color = img.getpixel((coord_x, coord_y))

                    if len(color) == 4:
                        color = (color[0], color[1], color[2])

                    if color not in color_list:
                        color_list.append(color)
                        size_list.append(1)

            chosen_color = EnvType.EMPTY.value

            if EnvType.OBSTACLE.value in color_list:
                chosen_color = EnvType.OBSTACLE.value
            elif EnvType.START.value in color_list and start is None:
                chosen_color = EnvType.START.value
                start = (x, y)
            elif EnvType.END.value in color_list:
                chosen_color = EnvType.END.value
                end.append((x, y))

            env_type = get_environment_type_from_value(chosen_color)

            if env_type is not None:
                env.set_tile(x, y, env_type)

    for x in range(width_tiles + 2):
        env.set_tile(x, 0, EnvType.OBSTACLE)
        env.set_tile(x, height_tiles + 1, EnvType.OBSTACLE)

    for y in range(height_tiles + 2):
        env.set_tile(0, y, EnvType.OBSTACLE)
        env.set_tile(width_tiles + 1, y, EnvType.OBSTACLE)

    end_node_clusters = []

    for end_node in end:
        cluster_id = -1

        for i in range(len(end_node_clusters)):
            if cluster_id != -1:
                break

            for other_end_node in end_node_clusters[i]:
                if abs(end_node[0] - other_end_node[0]) <= 1 and \
                        abs(end_node[1] - other_end_node[1]) <= 1:
                    cluster_id = i
                    end_node_clusters[i].append(end_node)
                    break

        if cluster_id == -1:
            end_node_clusters.append([end_node])

    end_nodes = []

    for cluster in end_node_clusters:
        avg_x, avg_y = 0, 0

        for node in cluster:
            avg_x += node[0]
            avg_y += node[1]

        avg_x, avg_y = avg_x // len(cluster), avg_y // len(cluster)

        end_nodes.append((avg_x, avg_y))

    env.set_start_end(start, end_nodes)

    return env
