import argparse
import logging

import ezdxf as dx
from networkx import write_yaml

from dxf_reader.hospital_dxf import DXF
from graph.extract_grid_from_dxf import get_grid
from graph.extract_grid_from_dxf import mark_exterior
from graph.graph_sparsifier import remove_small_components
from graph.graph_sparsifier import sparsify_graph
from graph.grid_to_graph_converter import make_graph_from_grid
from graph.labels_computer import propagate_labels
from graph_to_svg.svg_saver import export_graph_overlay_on_cad
from post_formatting.graph_serializer import make_4d_nodes
from util.constants import GRID_RATIO
from util.constants import MIN_COMPONENT_SIZE
from util.constants import SPARSITY_LEVEL

def show_all_entity_types(drawing_obj):
    a_set = set()
    for entity in drawing_obj.modelspace():
        a_set.add(type(entity))
    
    for a in a_set:
        print(a)


def extract_graph_from_dxf(architecture_filename, label_filename, outfile, building_name, step_size=None):
    """Converts an architecture CAD file into a graph with nodes and edges, then
    saves this graph as an SVG. Handles inputs in .dxf format only.

    :param architecture_filename: Name of the dxf file with walls, and doors.
    :param label_filename: Name of the dxf file with label information (This
           can be the same as architecture_filename)
    :param outfile: Name of the output svg file. This file will have the
           computed graph overlayed on the floor plan.
    :return: a graph representation of the CAD file.
    """
    floor_architecture = dx.readfile(architecture_filename)
    floor_labels = dx.readfile(label_filename)
    dxf_info = DXF(
        floor_architecture=floor_architecture,
        floor_labels=floor_labels,
        step_size=step_size,
    )

    grid = get_grid(dxf_info)
    mark_exterior(grid)

    graph = make_graph_from_grid(grid, dxf_info.room_labels)
    logging.info("edges added")
    sparsified_graph = sparsify_graph(graph, SPARSITY_LEVEL)
    logging.info("graph_sparsified")
    large_components_graph = remove_small_components(
        sparsified_graph,
        minsize=MIN_COMPONENT_SIZE,
    )
    propagate_labels(large_components_graph)

    export_graph_overlay_on_cad(
        dxf_info,
        large_components_graph,
        int(dxf_info.step_size/GRID_RATIO),
        dxf_info.new_canvas_dimensions,
        f"{outfile}.svg"
    )

    graph_4d = make_4d_nodes(large_components_graph, floor=outfile.split("/")[-1], building=building_name)
    write_yaml(graph_4d, f"{outfile}.yaml")
    logging.info(f"{outfile} created")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-fa', '--architecture_filename', type=str, default="cad_files/RoyCarver/Architecture/RCARLL.dxf", help="path to input architecture file")
    parser.add_argument('-fl', '--label_filename', type=str, default="cad_files/RoyCarver/Space/RCSPLL.dxf", help="path to input label file")
    parser.add_argument('-o', '--outfile', type=str, default="../Results/graphLLRC" ,help="path to output file")
    parser.add_argument('-v', '--verbose', action="store_true", help='turn verbose mode on')
    parser.add_argument('-vv', '--very_verbose', action="store_true", help='turn debug mode on')
    parser.add_argument('-sz', '--step_size', type=int, help="Supply a step size")
    parser.add_argument('-bl', '--building_name', type=str, default="RCARLL", help="The name of the building for this CAD file")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.very_verbose:
        logging.basicConfig(level=logging.DEBUG)

    extract_graph_from_dxf(
        architecture_filename=args.architecture_filename,
        label_filename=args.label_filename,
        outfile=args.outfile,
        step_size=args.step_size,
        building_name=args.building_name,
    )

if __name__ == "__main__":
    main()

