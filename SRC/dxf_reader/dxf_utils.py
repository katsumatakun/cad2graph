import math
from typing import List, Tuple


def generate_arc_angles(
        start_angle: float,
        end_angle: float,
        inc: int,
) -> List[float]:
    """Generates angles between start_angle and end_angle that are an
    an increment of `inc` apart, for drawing a polyline that will be used
    to approximate an arc.

    :param start_angle: The start angle (in degrees) of the arc.
    :param end_angle: The end angle in (in degrees) of the arc.
    :param inc: The increment spacing between the angles returned.
    :return: A list of angles between start_angle and end_angle that are
             an increment of `inc` apart.
    """
    start_angle %= 360
    end_angle %= 360
    angles = []
    cur_angle = start_angle
    angles.append(start_angle)
    while not (end_angle-inc <= cur_angle <= end_angle+inc):
        cur_angle = (cur_angle+inc) % 360
        angles.append(cur_angle)
    angles.append(end_angle)

    return angles


def is_relevant_layer(cur_layer: str, relevant_layers: List[str]) -> bool:
    """Returns True (False) if the cur_layer is (not) in the list of relevant
    layers.

    :param cur_layer: The layer to search for.
    :param relevant_layers: A list of relevant layers.
    :return:
    """
    for layer in relevant_layers:
        if layer in cur_layer:
            return True
    return False


def apply_negative_rotation_to_points(
        rotation: float,
        points: List[Tuple[float]],
):
    rotation = -1*rotation
    rotation = rotation / 180 * math.pi
    rotated_points = []
    for point in points:
        rotated_points.append(
            (
                point[0] * math.cos(rotation) + point[1] * math.sin(rotation),
                -1*point[0] * math.sin(rotation) + point[1] * math.cos(rotation),
            )
        )
    return rotated_points


def apply_scale_to_points(
        scale: Tuple[float],
        points: List[Tuple[float]],
):
    return [(p[0]*scale[0], p[1]*scale[1]) for p in points]


def remove_offsets_from_points(
        offsets: List[float],
        points: List[Tuple[float]],
):
    return [(p[0]-offsets[0], p[1]-offsets[1]) for p in points]
