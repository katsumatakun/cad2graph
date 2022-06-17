import logging
import math
import statistics
from typing import List, Tuple

from dxfgrabber.drawing import Drawing

from dxf_reader.dxf_to_shapely_objects import get_shapely_objects_from_relevant_layers
from dxf_reader.dxf_utils import is_relevant_layer
from dxf_reader.step_size_estimation import get_arcs, get_polylines
from util.constants import DEFAULT_WALL_LAYERS, DEFAULT_DOOR_LAYERS, DEFAULT_LABEL_LAYERS, GRID_RATIO
from util.data_containers import Point, RoomInfo

import math

class DXF:

    def __init__(self, floor_architecture: Drawing, floor_labels: Drawing, step_size: int=None):
        self.floor_architecture = floor_architecture
        self.floor_labels = floor_labels
        
        self.step_size = step_size if step_size else self.get_step_size()
        print("step_size", self.step_size)
        
        canvas_limits, offsets = get_canvas_size(floor_architecture, DEFAULT_WALL_LAYERS)
        
        self.offsets = offsets
        self.new_canvas_dimensions = [
            canvas_limits[0]-self.offsets[0],
            canvas_limits[1]-self.offsets[1],
        ]
        
        self.walls = self.get_walls()
        self.doors = self.get_doors()
        self.room_labels = self.get_all_roomlabels()
        logging.info(f"step_size {self.step_size}")

    def get_walls(self):
        walls = get_shapely_objects_from_relevant_layers(
            dxf=self.floor_architecture,
            relevant_layers=DEFAULT_WALL_LAYERS,
            offsets=self.offsets,
        )

        return walls

    def get_doors(self):
        doors = get_shapely_objects_from_relevant_layers(
            dxf=self.floor_architecture,
            relevant_layers=DEFAULT_DOOR_LAYERS,
            offsets=self.offsets,
        )
        return doors

    def get_step_size(self):
        """Estimates a step size for the cad file.
        If the step size is not defined, we estimate the step size by
        taking the median of all

        :return:
        """
        door_layer_polylines = get_polylines(self.floor_architecture, relevant_layers=DEFAULT_DOOR_LAYERS)
        door_layer_polylines += get_arcs(self.floor_architecture, relevant_layers=DEFAULT_DOOR_LAYERS)
        lens = []
        # print(len(door_layer_polylines))
        for polyline in door_layer_polylines:
            door_lens = []
            for p_i, p_f in zip(polyline.coords[:-1], polyline.coords[1:]):
                door_lens.append(math.hypot(
                    p_i[0]-p_f[0],
                    p_i[1]-p_f[1],
                ))
            lens.append(max(door_lens))
        return round(statistics.median(lens), 0)

    def get_all_roomlabels(self):
        room_labels = {}
        leader_positions = []
        for entity in self.floor_labels.modelspace():
            if is_relevant_layer(entity.dxf.layer, DEFAULT_LABEL_LAYERS) and entity.dxftype() == "LEADER":
                leader_vertices = [x for x in entity.get_vertices()]
                leader_start = Point(
                    x=int((leader_vertices[-1][0]-self.offsets[0])/int(self.step_size/GRID_RATIO)),
                    y=int((leader_vertices[-1][1]-self.offsets[1])/int(self.step_size/GRID_RATIO)),
                )

                leader_end = Point(
                    x=int((leader_vertices[0][0]-self.offsets[0])/int(self.step_size/GRID_RATIO)),
                    y=int((leader_vertices[0][1]-self.offsets[1])/int(self.step_size/GRID_RATIO)),
                )
                leader_positions.append((leader_start, leader_end))

        for entity in self.floor_labels.modelspace():
            if is_relevant_layer(entity.dxf.layer, DEFAULT_LABEL_LAYERS) and entity.dxftype() == "INSERT":
                # these are room labels
                label_pos = Point(
                    x=int((entity.dxf.insert[0]-self.offsets[0])/int(self.step_size/GRID_RATIO)),
                    y=int((entity.dxf.insert[1]-self.offsets[1])/int(self.step_size/GRID_RATIO)),
                )
                prev_label_pos = label_pos
                label_pos = move_label_if_leader_found(label_pos, leader_positions)
                details = {}
                for attrib in entity.attribs():
                    details[attrib.dxf.tag] = attrib.dxf.text

                room_labels[label_pos] = RoomInfo(
                    room_label=details["RMNU"] if "RMNU" in details else "NONAME",
                    details=details,
                )

        logging.info(f"room_labels {len(room_labels)}")
        return room_labels


def get_canvas_size(
        drawing: Drawing,
        relevant_layers: List[str],
) -> Tuple[List[int], List[int]]:
    line_x_values = []
    line_y_values = []

    relevant_objects = get_shapely_objects_from_relevant_layers(
        dxf=drawing,
        relevant_layers=["EXWALL"],

    )

    for entity in relevant_objects:
        line_x_values.extend([entity.bounds[0], entity.bounds[2]])
        line_y_values.extend([entity.bounds[1], entity.bounds[3]])

    canvas_width_max = int(max(line_x_values))
    canvas_length_max = int(max(line_y_values))
    canvas_width_min = int(min(line_x_values))
    canvas_length_min = int(min(line_y_values))

    offsets = [canvas_width_min-100, canvas_length_min-100]
    canvas_limits = [canvas_width_max+100, canvas_length_max+100]

    # print(offsets, canvas_limits)
    return canvas_limits, offsets


def move_label_if_leader_found(
        label_pos: Point,
        leader_positions: List[Tuple[Point]],
):
    """It moves a label to a new location if a close enough
    'Leader' is found.

    :param label_pos: Position of the label.
    :param leader_positions: A list of start and end positions of all
           'leaders' found in the file.
    :return: The updated position of the label if a leader is found close
             enough, otherwise its the same position.
    """
    minimum_distance = l2norm(leader_positions[0][0], label_pos)
    minimum_distance_point = leader_positions[0][1]
    for leader_position in leader_positions[1:]:
        cur_distance = l2norm(label_pos, leader_position[0])
        if cur_distance < minimum_distance:
            minimum_distance = cur_distance
            minimum_distance_point = leader_position[1]

    if math.sqrt(minimum_distance) < 7:
        return minimum_distance_point
    else:
        return label_pos


def l2norm(
        p1: Point,
        p2: Point,
):
    return (p1.x-p2.x)**2 + (p1.y-p2.y)**2
