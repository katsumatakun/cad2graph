import math
from typing import List

from dxfgrabber.drawing import Drawing
from shapely.geometry import LineString

from dxf_reader.dxf_utils import is_relevant_layer


def get_arcs(
        dxf: Drawing,
        relevant_layers: List[str],
        offsets: List[int]= (0, 0),
):
    """Extracts arcs from the CAD file, and approximates them with a line.

    :param dxf:
    :param relevant_layers:
    :param offsets:
    :return:
    """
    arc_lines = []

    for entity in dxf.entities:
        if  entity.dxftype == "ARC" and is_relevant_layer(
                entity.layer,
                relevant_layers,
        ):
            arc_line = LineString([
                (
                    entity.center[0] + entity.radius*math.cos(entity.start_angle/180*math.pi)-offsets[0],
                    entity.center[1] + entity.radius*math.sin(entity.start_angle/180*math.pi)-offsets[1],
                ),
                (
                    entity.center[0] + entity.radius*math.cos(entity.end_angle/180*math.pi)-offsets[0],
                    entity.center[1] + entity.radius*math.sin(entity.end_angle/180*math.pi)-offsets[1],
                ),
            ])
            arc_lines.append(arc_line)

    return arc_lines


def get_polylines(
        dxf: Drawing,
        relevant_layers: List[str],
        offsets: List[int]= (0, 0),
):
    polylines = []
    print(relevant_layers)
    # print(list(dxf.entities))
    for entity in dxf.entities:
        # print(dir(entity), type(entity))
        if entity.dxftype() in ["LWPOLYLINE", "POLYLINE"] and is_relevant_layer(
                entity.dxf.layer, relevant_layers,
        ) :
            polylines.append(
                LineString(
                    map(
                        lambda x: (x[0]-offsets[0], x[1]-offsets[1]),
                        entity.points().__enter__()
                    )
                )
            )
    return polylines


def get_lines(
        dxf: Drawing,
        relevant_layers: List[str],
        offsets: List[int]= (0, 0),
):
    lines = []
    for entity in dxf.entities:
        if is_relevant_layer(
                entity.dxf.layer,
                relevant_layers,
        ) and entity.dxftype() == "LINE":
            lines.append(
                LineString([
                    (int(entity.start[0]-offsets[0]), int(entity.start[1]-offsets[1])),
                    (int(entity.end[0]-offsets[0]), int(entity.end[1]-offsets[1])),
                ])
            )
    return lines
