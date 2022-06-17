import math
from typing import List, Union, Tuple, Optional

from dxfgrabber.dxfentities import Face, Solid, Trace, Line, Polyline, LWPolyline, Arc, DXFEntity, Circle, Insert
from ezdxf.drawing import Drawing
from shapely.geometry import Polygon, LineString
from shapely.geometry.base import BaseGeometry

from dxf_reader.dxf_utils import generate_arc_angles, is_relevant_layer, apply_negative_rotation_to_points, \
    apply_scale_to_points, remove_offsets_from_points
from util.constants import DEFAULT_WALL_LAYERS


def get_shapely_objects_from_block(
        dxf: Drawing,
        insert_entity: Insert,
        offsets: List[int],
        previous_rotation: float,
        relevant_layers: List[str] = DEFAULT_WALL_LAYERS,
) -> List[BaseGeometry]:
    """Extracts shapely objects from all currently handled dxf entities
    inside this block insert entity.

    :param dxf: A dxf drawing obect
    :param insert_entity: The insert entity that we need to extract
           shapely objects from.
    :param offsets: The offsets that we inherit from reading the dxf file.
    :param previous_rotation: If this insert entity is inside another insert
           then we need to remove the rotation from the previous insert
           entity as well.
    :param relevant_layers: The layers we want to extract shapely objects from.

    :return: A list of all extracted shapely objects.
    """
    block = dxf.blocks[insert_entity.dxf.name]
    scale = [insert_entity.dxf.xscale, insert_entity.dxf.yscale]
    block_offsets = [offsets[0] - insert_entity.dxf.insert[0], offsets[1] - insert_entity.dxf.insert[1]]
    block_objects = []
    for entity in block:
        if entity.dxftype == "INSERT":

            sub_entities = get_shapely_objects_from_block(
                dxf=dxf,
                insert_entity=entity,
                offsets=block_offsets,
                previous_rotation=previous_rotation+insert_entity.dxf.rotation,
                relevant_layers=relevant_layers,
            )
            block_objects.extend(sub_entities)
        else:
            shapely_object = get_shapely_object_from_entity(
                entity=entity,
                offsets=block_offsets,
                scale=scale,
                rotation=previous_rotation+insert_entity.dxf.rotation,
            )
            if shapely_object:
                block_objects.append(shapely_object)
    return block_objects


def get_polygon_from_shape(
        shape: Union[Face, Solid, Trace],
        offsets: List[int],
        scale: Tuple[int],
        rotation: float,
) -> Polygon:
    """Converts the dxfgrabber polygon object into a shapely Polygon.
    We currently only handle three dxfgrabber polygons: Face, Solid, Trace

    :param shape: The dxfgrabber polygon(Face, Solid or Trace) object that needs
           to be converted.
    :param offsets: Offsets that we inherit by reading the dxf file.
    :param scale: If the shape is inside an Insert object, it will have a
           scaling factor which must be applied to all objects inside it.
    :param rotation: (in degrees) If the shape is inside an Insert object,
           the insert might be rotated with respect to the original axes
           and this rotation must be removed.
    :return: A shapely polygon object.
    """
    points = apply_scale_to_points(scale, shape.dxf.points)
    points = apply_negative_rotation_to_points(rotation, points)
    points = remove_offsets_from_points(offsets, points)
    return Polygon(points)


def get_linestring_from_line(
        line: Line,
        offsets: List[int],
        scale: Tuple[int],
        rotation: float,
) -> LineString:
    """Converts the dxfgrabber line object into a shapely linestring.

    :param line: The dxfgrabber line object that needs to be converted.
    :param offsets: Offsets that we inherit by reading the dxf file.
    :param scale: If the line is inside an Insert object, it will have a
           scaling factor which must be applied to all objects inside it.
    :param rotation: (in degrees) If the line is inside an Insert object,
           the insert might be rotated with respect to the original axes
           and this rotation must be removed.
    :return: A shapely linestring object.
    """
    line_points = [line.dxf.start, line.dxf.end]
    points = apply_scale_to_points(scale, line_points)
    points = apply_negative_rotation_to_points(rotation, points)
    points = remove_offsets_from_points(offsets, points)
    return LineString(points)


def get_linestring_from_polyline(
        polyline: Union[Polyline, LWPolyline],
        offsets: List[int],
        scale: Tuple[int],
        rotation: float,
) -> LineString:
    """Converts the dxfgrabber polyline object into a shapely linestring.
    (NOTE: polyline bulges were not implemented)

    :param polyline: The dxfgrabber polyline object that needs to be converted.
    :param offsets: Offsets that we inherit by reading the dxf file.
    :param scale: If the polyline is inside an Insert object, it will have a
           scaling factor which must be applied to all objects inside it.
    :param rotation: (in degrees) If the polyline is inside an Insert object,
           the insert might be rotated with respect to the original axes
           and this rotation must be removed.
    :return: A shapely linestring object.
    """
    points = polyline.points() if polyline.dxftype() == "POLYLINE" else polyline.get_points()
    points = apply_scale_to_points(scale, points)
    points = apply_negative_rotation_to_points(rotation, points)
    points = remove_offsets_from_points(offsets, points)
    return LineString(points)



def get_linestring_from_circle(
        circle: Circle,
        offsets: List[int],
        scale: Tuple[int],
) -> LineString:
    """Converts the dxfgrabber Circle object into a shapely linestring.
    The linestring is a polyline that approximates the arc by having
    segments at each 5 degree interval.

    :param circle: The dxfgrabber Circle object that needs to be converted.
    :param offsets: Offsets that we inherit by reading the dxf file.
    :param scale: If the circle is inside an Insert object, it will have a
           scaling factor which must be applied to all objects inside it.
    :return: A shapely linestring object.
    """
    circle_points = []
    angles = range(0, 361, 5)
    for angle in angles:
        circle_points.append(
            (
                 circle.dxf.center[0] + scale[0]*circle.dxf.radius * math.cos(angle / 180 * math.pi) - offsets[0],
                 circle.dxf.center[1] + scale[1]*circle.dxf.radius * math.sin(angle / 180 * math.pi) - offsets[1],
            )
        )
    circle_line = LineString(circle_points)
    return circle_line


def get_linestring_from_arc(
        arc: Arc,
        offsets: List[int],
        scale: Tuple[int],
        rotation: float,
) -> Optional[LineString]:
    """Converts the dxfgrabber Arc object into a shapely linestring.
    The linestring is a polyline that approximates the arc by having
    segments at each 5 degree interval.

    :param arc: The dxfgrabber Arc object that needs to be converted.
    :param offsets: Offsets that we inherit by reading the dxf file.
    :param scale: If the arc is inside an Insert object, it will have a
           scaling factor which must be applied to all objects inside it.
    :param rotation: (in degrees) If the Arc is inside an Insert object,
           the insert might be rotated with respect to the original axes
           and this rotation must be removed.
    :return: A shapely linestring object.
    """
    arc_points = []
    angles = generate_arc_angles(
        arc.dxf.start_angle,
        arc.dxf.end_angle,
        5,
    )
    if arc.dxf.extrusion == (0.0, 0.0, -1.0):
        # for angle in angles:
        #     # angle = 270+angle
        #     arc_points.append(
        #         (
        #             arc.center[0] + arc.radius * math.cos(angle / 180 * math.pi),
        #             arc.center[1] - arc.radius * math.sin(angle / 180 * math.pi),
        #         )
        #     )
        # arc_points = apply_negative_rotation_to_points(180, arc_points)
        return None
    else:
        for angle in angles:
            arc_points.append(
                (
                    arc.dxf.center[0] + arc.dxf.radius * math.cos(angle / 180 * math.pi),
                    arc.dxf.center[1] + arc.dxf.radius * math.sin(angle / 180 * math.pi),
                )
            )
    arc_points = apply_scale_to_points(scale, arc_points)
    arc_points = apply_negative_rotation_to_points(rotation, arc_points)
    arc_points = remove_offsets_from_points(offsets, arc_points)

    return LineString(arc_points)


def get_shapely_object_from_entity(
        entity: DXFEntity,
        offsets: List[int],
        scale: Tuple[int]= (1, 1),
        rotation: float = 0,
) -> Union[LineString, Polygon]:
    """Takes a dxf entity and converts it to a shapely object. We currently
    handle the following dxf entities: FACE, SOLID, TRACE, LINE, POLYLINE,
    LWPOLYLINE, ARC.

    :param entity: The dxf entity that we need to convert.
    :param offsets: The offsets that we inherit from reading the dxf file.
    :param scale: If the entity is inside an Insert object, it will have a
           scaling factor which must be applied to all objects inside it.
    :param rotation: (in degrees) If the entity is inside an Insert object,
           the insert might be rotated with respect to the original axes
           and this rotation must be removed.
    :return: A shapely geometric object. This is either a linestring or a
             polygon.
    """
    if entity.dxftype() in {"FACE", "SOLID", "TRACE"}:
        return get_polygon_from_shape(entity, offsets, scale, rotation)
    if entity.dxftype() == "LINE":
        return get_linestring_from_line(entity, offsets, scale, rotation)
    if entity.dxftype() in {"POLYLINE", "LWPOLYLINE"}:
        return get_linestring_from_polyline(entity, offsets, scale, rotation)
    if entity.dxftype() == "ARC":
        return get_linestring_from_arc(entity, offsets, scale, rotation)
    if entity.dxftype() == "CIRCLE":
        return get_linestring_from_circle(entity, offsets, scale)


def get_shapely_objects_from_relevant_layers(
        dxf: Drawing,
        relevant_layers: List[str],
        offsets: List[int] = (0, 0),
) -> List[BaseGeometry]:
    """Extracts shapely objects from the relevant layers in the dxf Drawing.
    We currently handle the following dxf entities: FACE, SOLID, TRACE, LINE,
    POLYLINE, LWPOLYLINE, ARC.

    :param dxf: A dxf drawing obect
    :param relevant_layers: The layers we want to extract shapely objects from.
    :param offsets: The offsets that we inherit from reading the dxf file.
    :return: A list of all extracted shapely objects.
    """
    shapely_objects = []
    for entity in dxf.modelspace():
        if is_relevant_layer(
                entity.dxf.layer,
                relevant_layers,
        ):
            if entity.dxftype() == "INSERT":
                rel_ent = get_shapely_objects_from_block(
                    dxf=dxf,
                    insert_entity=entity,
                    offsets=offsets,
                    previous_rotation=0,
                    relevant_layers=relevant_layers,
                )
                shapely_objects.extend(
                    rel_ent
                )
            else:
                shapely_object = get_shapely_object_from_entity(entity, offsets)
                if shapely_object:
                    shapely_objects.append(shapely_object)
    return shapely_objects
