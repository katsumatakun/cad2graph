from typing import Dict
from typing import List

from networkx import Graph

from util.data_containers import Node_4d
from util.data_containers import Node
from util.data_containers import Point
from util.data_containers import RoomInfo
from util.data_containers import SpaceType


def make_graph_from_grid(
        grid: List[List[SpaceType]],
        room_infos: Dict[Point, RoomInfo],
        floor = 0,
        building = ""
):
    graph = Graph()
    add_nodes_from_grid(graph, grid, room_infos, floor, building)
    add_edges_from_grid(graph)

    return graph


def add_nodes_from_grid(
        graph: Graph,
        grid: List[List[SpaceType]],
        room_infos: Dict[Point, RoomInfo],
        floor = 0,
        building = ""
        
):
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] in {SpaceType.OPEN, SpaceType.DOOR}:
                cur_node = Node(x=i, y=j)
                node_to_add = Node_4d(x=i, y=j, floor=floor, building=building)
                if cur_node in room_infos:
                    print("room_info")
                    room_label = room_infos[cur_node].room_label
                    node_details = room_infos[cur_node].details
                    print("node_details", node_details)
                else:
                    room_label = ""
                    node_details = {}
                node_details["room_label"] = room_label
                node_details["type"] = grid[i][j]

                graph.add_node(
                    node_to_add,
                    **node_details,
                )


def add_edges_from_grid(graph: Graph):
    for u in graph.nodes:
        # edge_list = {
        #     (Node(u.x-1, u.y), 1),
        #     (Node(u.x+1, u.y), 1),
        #     (Node(u.x, u.y+1), 1),
        #     (Node(u.x, u.y-1), 1),
        #     (Node(u.x-1, u.y-1), 1.4),
        #     (Node(u.x+1, u.y+1), 1.4),
        #     (Node(u.x-1, u.y+1), 1.4),
        #     (Node(u.x+1, u.y-1), 1.4),
        # }
        edge_list = {
            (Node_4d(u.x-1, u.y, u.floor, u.building), 1),
            (Node_4d(u.x+1, u.y, u.floor, u.building), 1),
            (Node_4d(u.x, u.y+1, u.floor, u.building), 1),
            (Node_4d(u.x, u.y-1, u.floor, u.building), 1),
            (Node_4d(u.x-1, u.y-1, u.floor, u.building), 1.4),
            (Node_4d(u.x+1, u.y+1, u.floor, u.building), 1.4),
            (Node_4d(u.x-1, u.y+1, u.floor, u.building), 1.4),
            (Node_4d(u.x+1, u.y-1, u.floor, u.building), 1.4),
        }

        for v, weight in edge_list:
            if v in graph.nodes:
                if graph.nodes[u]["type"] == SpaceType.DOOR or \
                                graph.nodes[v]["type"] == SpaceType.DOOR:
                    weight2 = 1000
                    edge_type = "door"
                else:
                    weight2 = weight
                    edge_type = "normal"
                graph.add_edge(
                    u,
                    v,
                    type=edge_type,
                    weight=weight,
                    weight2=weight2,
                )
