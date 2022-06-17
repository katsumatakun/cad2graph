# -*- coding: utf-8 -*-

import argparse
import logging

import networkx as nx
import ezdxf as dx
from networkx import write_yaml
import numpy as np
import json

from dxf_reader.hospital_dxf import DXF
from graph.extract_grid_from_dxf import get_grid
from graph.extract_grid_from_dxf import mark_exterior
from graph.graph_sparsifier import remove_small_components, remove_components_without_labels
from graph.graph_sparsifier import sparsify_graph
from graph.grid_to_graph_converter import make_graph_from_grid
from graph.graph_utils import collect_labelled_nodes, collect_stair_nodes, collect_elev_nodes
from graph.labels_computer import propagate_labels
from graph_to_svg.svg_saver import export_graph_overlay_on_cad
from post_formatting.graph_serializer import make_4d_nodes
from util.constants import GRID_RATIO
from util.constants import MIN_COMPONENT_SIZE
from util.constants import SPARSITY_LEVEL
from networkx import shortest_path
from networkx import shortest_path_length

#'RMNAC'=what kind of room
#'FLR' = floor

stairs = {}
elevs = {}

graphs_each_floor = []


floors = ["LL"]
building = "RoyCarver"
prefix = "RC"
for i in floors:
    floor_architecture = dx.readfile("cad_files/"+building+"/Architecture/"+prefix+"AR"+str(i)+".dxf")
    floor_labels = dx.readfile("cad_files/"+building+"/Space/"+prefix+"SP"+str(i)+".dxf")
    
    
    print("load_data")
    step_size = None 
    dxf_info = DXF(
        floor_architecture=floor_architecture,
        floor_labels=floor_labels,
        step_size=step_size,
    )
    
    print("hosp dxf")
    floor = i
    
    grid = get_grid(dxf_info)
    
    print("grid")
    mark_exterior(grid)
    graph = make_graph_from_grid(grid, dxf_info.room_labels, floor, building)
    print("graph")
    
    sparsified_graph = sparsify_graph(graph, SPARSITY_LEVEL)
    
    print("sparsify")
    large_components_graph = remove_small_components(
        sparsified_graph,
        minsize=MIN_COMPONENT_SIZE,
    )
    
    # dis_dic = collect_path_len_bw_labeled_nodes(large_components_graph)
    # plot_dis(dis_dic)
    
    # dis_dic2 = collect_path_len_bw_labeled_nodes(large_components_graph, "weight2")
    # plot_dis(dis_dic2, "weight2")

    

    
   
    l_nodes = collect_labelled_nodes(large_components_graph)
    s_nodes = collect_stair_nodes(l_nodes)
    e_nodes = collect_elev_nodes(l_nodes)
    
    for node in s_nodes:
        num = node[1]["room_label"][-5:]
        if node[1]["room_label"][-5:] not in stairs:
            lst = [(node[0],node[1]["room_label"])]
            stairs[num] = lst
        else:
            stairs[num].append((node[0],node[1]["room_label"]))
    elevs[i] = e_nodes
    
            
    propagate_labels(large_components_graph)
    
    large_components_graph = remove_components_without_labels(large_components_graph)
    graphs_each_floor.append(large_components_graph)
    
    nx.write_edgelist(large_components_graph, "../Results/"+prefix+str(i)+"_edgelist.txt", data=["type", "weight2"])
    
    print("edge list")
    node_dic = {}
    nodes = large_components_graph.nodes
    for node in nodes:
        nodes[node]["type"] = str(nodes[node]["type"])
        node_dic[str(node)] = nodes[node]
    
    print("node dic")
    json.dump(node_dic, open("../Results/"+prefix+str(i)+"_nodelist.json", "w"))
    
    print("svg out")
    export_graph_overlay_on_cad(
    dxf_info,
    large_components_graph,
    int(dxf_info.step_size/GRID_RATIO),
    dxf_info.new_canvas_dimensions,
    "../Results/graph"+str(i)+prefix+".svg"
    )



    
    
json.dump(stairs, open("../Results/stairs_"+prefix+".json", 'w'))
json.dump(elevs, open("../Results/elevs_"+prefix+".json", 'w'))

    

####from util.data_containers import Node_4d
####from str to Node_4d, use eval()
