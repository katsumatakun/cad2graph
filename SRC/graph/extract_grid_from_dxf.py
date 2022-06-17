import logging
from typing import List

from rtree.index import Index
from shapely.geometry import Polygon
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry

from dxf_reader.hospital_dxf import DXF
from util.constants import DELETE_LINE_SIZE
from util.constants import GRID_RATIO
from util.constants import OUTSIDE_COLOR
from util.data_containers import Point
from util.data_containers import SpaceType

MAX_CHANGES_IN_DIRECTION = 1


def mark_exterior(grid: List[List[int]]):
    """Removes the exterior of the floor by marking it (as OUTSIDE_COLOR).
    We mark the exterior as outside by flood filling from the edges of the
    grid, but we use DELETE_LINE_SIZE as the width for our flood fill.

    :param grid: A grid representation of space in the CAD file, where 0's
           represent empty space.
    """
    for i in range(len(grid)):
        move_line_and_delete_horizontal(
            grid,
            Point(i, 0),
            1,
            MAX_CHANGES_IN_DIRECTION,
        )
        move_line_and_delete_horizontal(
            grid,
            Point(i, len(grid[0])-1),
            -1,
            MAX_CHANGES_IN_DIRECTION,
        )

    for j in range(len(grid[0])):
        move_line_and_delete_vertical(
            grid,
            Point(0, j),
            1,
            MAX_CHANGES_IN_DIRECTION,
        )
        move_line_and_delete_vertical(
            grid,
            Point(len(grid)-1, j),
            -1,
            MAX_CHANGES_IN_DIRECTION,
        )


def move_line_and_delete_vertical(
        grid: List[List[int]],
        pos: Point,
        direction: int,
        changes_in_direction: int,

):
    """This is a function that moves a vertical line in a horizontal direction
    from the edge of the drawing. If the whole vertical line is empty, it
    marks it as being outside the building and continues to move in. This
    function also calls move_line_and_delete_horizontal if
    changes_in_direction > 0.

    :param grid: A grid representation of space in the CAD file, where 0's
           represent empty space.
    :param pos: current position of the vertical line
    :param direction: the current direction we are moving in, can be -1 or 1.
    :param changes_in_direction: the number of changes in direction we can still
           make.
    """
    while True:
        if not 0 <= pos.y+DELETE_LINE_SIZE <= len(grid[0]):
            return
        if not 0 <= pos.x < len(grid):
            return
        for k in range(pos.y, pos.y+DELETE_LINE_SIZE):
            if grid[pos.x][k] in {SpaceType.WALL, SpaceType.DOOR}:
                return
        for k in range(pos.y, pos.y+DELETE_LINE_SIZE):
            grid[pos.x][k] = OUTSIDE_COLOR
        pos = Point(pos.x+direction, pos.y)
        if changes_in_direction > 0:
            move_line_and_delete_horizontal(
                grid, pos, 1, changes_in_direction-1,
            )
            move_line_and_delete_horizontal(
                grid, pos, -1, changes_in_direction-1,
            )


def move_line_and_delete_horizontal(
        grid: List[List[int]],
        pos: Point,
        direction: int,
        changes_in_direction: int,

):
    """This is a function that moves a horizontal line in a vertical direction
    from the edge of the drawing. If the whole horizontal line is empty, it
    marks it as being outside the building and continues to move in. This
    function also calls move_line_and_delete_vertical if
    changes_in_direction > 0.

    :param grid: A grid representation of space in the CAD file, where 0's
           represent empty space.
    :param pos: current position of the vertical line.
    :param direction: the current direction we are moving in, can be -1 or 1.
    :param changes_in_direction: the number of changes in direction we can still
           make.
    """
    while True:
        if not 0 <= pos.x+DELETE_LINE_SIZE <= len(grid):
            return
        if not 0 <= pos.y < len(grid[0]):
            return
        for k in range(pos.x, pos.x+DELETE_LINE_SIZE):
            if grid[k][pos.y] in {SpaceType.WALL, SpaceType.DOOR}:
                return
        for k in range(pos.x, pos.x+DELETE_LINE_SIZE):
                grid[k][pos.y] = OUTSIDE_COLOR
        pos = Point(pos.x, pos.y+direction)
        if changes_in_direction > 0:
            move_line_and_delete_vertical(
                grid, pos, 1, changes_in_direction-1,
            )
            move_line_and_delete_vertical(
                grid, pos, -1, changes_in_direction-1,
            )


import math
def get_grid(
        dxf_to_graph: DXF,
) -> List[List[SpaceType]]:
    """Builds a grid representation of the CAD file by where the 0's represent
    empty space.

    :param dxf_to_graph: A DXF object which contains extracted features from
           the CAD file.
    :param grid_val: The value to assign to non-empty spaces
    :return: A list of lists where each end value is an int. This provides a
             grid representation of the CAD file.
    """
    grid_size = int(dxf_to_graph.step_size/GRID_RATIO)
    y_max, x_max = [int(lim/grid_size) for lim in dxf_to_graph.new_canvas_dimensions]
    grid = [[SpaceType.OPEN]*x_max for i in range(y_max+1)]
    grid_cells = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            grid_cells.append(
                box(
                    minx=i*grid_size,
                    miny=j*grid_size,
                    maxx=(i+1)*grid_size,
                    maxy=(j+1)*grid_size,
                )
            )

    logging.info("building R tree")
    rtree = Index()
    for pos, cell in enumerate(grid_cells):
        rtree.insert(pos, cell.bounds)

    _calculate_shape_intersections_with_grid_cells(
        shapes=dxf_to_graph.doors,
        space_type=SpaceType.DOOR,
        rtree=rtree,
        grid_cells=grid_cells,
        grid=grid,
        grid_size=grid_size,
    )

    _calculate_shape_intersections_with_grid_cells(
        shapes=dxf_to_graph.walls,
        space_type=SpaceType.WALL,
        rtree=rtree,
        grid_cells=grid_cells,
        grid=grid,
        grid_size=grid_size,
    )

    return grid


def _calculate_shape_intersections_with_grid_cells(
        shapes: List[BaseGeometry],
        space_type: SpaceType,
        rtree: Index,
        grid_cells: List[Polygon],
        grid: List[List[SpaceType]],
        grid_size: int,
):
    shape_id = 0
    percent_done = 0
    for shape in shapes:
        shape_id += 1
        if int(shape_id/len(shapes)*100) != percent_done:
            percent_done = int(shape_id/len(shapes)*100)
            logging.debug(f"making grid, adding {space_type}: {percent_done}% done")

        for pos in rtree.intersection(shape.bounds):
            cell = grid_cells[pos]
            try:
                if cell.intersection(shape):
                    grid[
                        int(cell.bounds[0]/grid_size)
                    ][
                        int(cell.bounds[1]/grid_size)
                    ] = space_type
            except Exception as e:
                print(e)
