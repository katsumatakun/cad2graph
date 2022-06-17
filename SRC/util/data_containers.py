from collections import namedtuple
from typing import NamedTuple
from enum import Enum

Point = namedtuple('Point', ['x', 'y'])
RoomInfo = namedtuple('RoomInfo', ['room_label', 'details'])
Node = namedtuple('Node', ['x', 'y'])
Node_4d = namedtuple('Node_4d', ['x', 'y', 'floor', 'building'])


class SpaceType(Enum):
    OPEN = 0
    WALL = 1
    DOOR = 2
