import functools
from typing import List

from networkx import Graph
from networkx import shortest_path
from networkx import shortest_path_length
from networkx import single_source_dijkstra_path_length
from networkx.exception import NetworkXNoPath
import numpy as np

from util.data_containers import Node


def is_neighborhood_marked(sparsified_graph, nhood):
    for node in nhood:
        if sparsified_graph.has_node(node):
            return True
    return False


@functools.lru_cache(maxsize=10000)
def compute_neighborhood_cached(
        G: Graph,
        source: Node,
        cutoff: int,
        weight: str='weight',
):
    """a memoized call to compute `cutoff`-hop neighborhoods.

    :param graph: The input graph.
    :param source: The source node to compute paths from.
    :param cutoff: The number of hops in the neighborhoods.
    :param weight: The name of the key providing weights for the edges.
    :return: Dict keyed by node to shortest path length from source.
    """
    return single_source_dijkstra_path_length(
        G=G,
        source=source,
        cutoff=cutoff,
        weight=weight,
    )


def shortest_path_less_than_cutoff(
        graph: Graph,
        source: Node,
        target: Node,
        cutoff: int,
):
    """Computes the shortest path between nodes source and target in graph
    and returns True iff its less than or equal to cutoff, False otherwise.

    :param graph: The input graph.
    :param source: The source node.
    :param target: The target node.
    :param cutoff: A cutoff for the maximum distance between source and target.
    :return: True/False indicating whether the distance between source and
             target is less than or equal to cutoff.
    """
    try:
        path = shortest_path(
            G=graph,
            source=source,
            target=target,
        )
        if len(path) <= cutoff:
            return path
        else:
            return []
    except NetworkXNoPath:
        return []


def add_graph_offsets(
        graph: Graph,
        offsets: List[int],
):
    graph_with_offsets = Graph()

    for node in graph.nodes:
        graph_with_offsets.add_node(
            Node(node.x+offsets[0], node.y+offsets[1]),
            **graph.nodes[node],
        )
    for edge in graph.edges:
        u, v = edge[0], edge[1]
        u1 = Node(u.x+offsets[0], u.y+offsets[1])
        v1 = Node(v.x+offsets[0], v.y+offsets[1])
        graph_with_offsets.add_edge(
            u=u1,
            v=v1,
            **graph.edges[edge],
        )
    return graph_with_offsets


def compute_hospital_graph_shortest_path(
        hospital_graph : Graph,
        room_label_1: str,
        room_label_2: str,
):
    room_id_1 = None
    room_id_2 = None
    for node in hospital_graph.nodes:
        if hospital_graph.nodes[node]["room_label"] == room_label_1:
            room_id_1 = node
            if room_id_2:
                return len(shortest_path(hospital_graph, room_id_1, room_id_2)) - 1
        if hospital_graph.nodes[node]["room_label"] == room_label_2:
            room_id_2 = node
            if room_id_1:
                return len(shortest_path(hospital_graph, room_id_1, room_id_2)) - 1


def add_edge_by_room_labels(
        hospital_graph: Graph,
        room_label_1: str,
        room_label_2: str,
):
    room_id_1 = None
    room_id_2 = None
    for node in hospital_graph.nodes:
        if hospital_graph.nodes[node]["room_label"] == room_label_1:
            room_id_1 = node
            if room_id_2:
                return hospital_graph.add_edge(
                    room_id_1,
                    room_id_2,
                    weight=1,
                    weight2=1,
                )
        if hospital_graph.nodes[node]["room_label"] == room_label_2:
            room_id_2 = node
            if room_id_1:
                return hospital_graph.add_edge(
                    room_id_1,
                    room_id_2,
                    weight=1,
                    weight2=1,
                )

def show_all_entity_types(drawing_obj):
    a_set = set()
    for entity in drawing_obj.modelspace():
        a_set.add(type(entity))
    
    for a in a_set:
        print(a)
        
def show_node_details(graph):
    for node in graph.nodes:
        print(node.details) 
        
def collect_labelled_nodes(sparsified_graph):
    dic = {}
    for node in sparsified_graph.nodes:
        if sparsified_graph.nodes[node]["room_label"]:
            dic[node] = sparsified_graph.nodes[node]
    return dic

def collect_stair_nodes(labeled_nodes):
    lst = []
    for key in labeled_nodes:
        if labeled_nodes[key]["RMNAC"] == "STAIR":
            lst.append((key, labeled_nodes[key]))
    return lst

def collect_elev_nodes(labeled_nodes):
    lst = []
    for key in labeled_nodes:
         if "ELEV" in labeled_nodes[key]["RMNAC"]:
            lst.append((key, labeled_nodes[key]["RMNAC"]))
    return lst
    
def collect_path_len_bw_labeled_nodes(sparsified_graph, weight="weight"):
    l_nodes = collect_labelled_nodes(sparsified_graph)
    dic = {}
    for source in l_nodes:
        for target in l_nodes:
            if (target, source) in dic:
                continue
            if source != target: 
                try:
                    path_len = shortest_path_length(
                    G=sparsified_graph,
                    source=source,
                    target=target,
                    weight=weight
                )
                    eu_dis = compute_distance(source, target)
                    dic[(source,target)] = (path_len, eu_dis)
                except:
                    continue
                
                
    return dic 

def compute_distance(node1, node2):
        
        x1 = node1[0]
        x2 = node2[0]
        y1 = node1[1]
        y2 = node2[1]
        return np.sqrt((x1-x2)**2+(y1-y2)**2)

def weight2_of_path(path, graph):
    edges_in_path = []
    for i in range(len(path)-1):
        edges_in_path.append((path[i],path[i+1]))
    edges = graph.edges
    total_weight = 0
    for e in edges_in_path:
        total_weight += edges[e]["weight"] 
    
    return total_weight

def set_of_RMNAC(labeled_nodes):
    a_set = set()
    for n in labeled_nodes:
        a_set.add(n[1]["RMNAC"])
    return a_set




import matplotlib.pyplot as plt
def plot_dis(dis_dic, weight = "weight"):
    
    fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
    plt.scatter(*zip(*dis_dic.values()))
    if weight == "weight":
        plt.xlabel("# hpos")
    else:
        plt.xlabel("weihgt2 distance")
    plt.ylabel("euclidean distance")
    fig.savefig("dis_scatter "+weight+".png")   # save the figure to file
    plt.close(fig)    # close the figure window