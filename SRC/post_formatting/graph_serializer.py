from networkx import Graph
from networkx import empty_graph

from util.data_containers import Node_4d


def make_graph_serializable(graph: Graph) -> Graph:
    """Makes the networkx graphs serializable so that they can be stored
    in a variety of ways.

    :param graph: a network x graph
    :return: a serializable networkx graph
    """
    serializable_graph = empty_graph()
    for node in graph.nodes:
        new_node_name = f"{node.x}-{node.y}"
        serializable_graph.add_node(
            new_node_name,
            **graph.nodes[node],
        )

    for edge in graph.edges:
        u, v = edge[0], edge[1]
        source = f"{u.x}-{u.y}"
        dest = f"{v.x}-{v.y}"
        serializable_graph.add_edge(
            source,
            dest,
            **graph.edges[edge],
        )
    return serializable_graph


def make_4d_nodes(
        graph: Graph,
        floor: str,
        building: str,
) ->  Graph:
    """Change the nodes in the graph so that they have a component for their
    floor and building as well. This is done so that multiple graphs can be
    easily composed.

    :param graph: a network x graph where the nodes are 2-dimensional with
           x and y values
    :param floor: the floor for this graph.
    :param building: the building for this graph.
    :return: a network x graph where the nodes have floor and building as well
             as the x and y coords
    """
    graph_4d = Graph()
    for node in graph.nodes:
        new_node = Node_4d(
            x=node.x,
            y=node.y,
            building=building,
            floor=floor,
        )
        graph_4d.add_node(
            new_node,
            **graph.nodes[node],
        )

    for edge in graph.edges:
        u, v = edge[0], edge[1]
        source = Node_4d(
            x=u.x,
            y=u.y,
            building=building,
            floor=floor,
        )
        dest = Node_4d(
            x=v.x,
            y=v.y,
            building=building,
            floor=floor,
        )
        graph_4d.add_edge(
            source,
            dest,
            **graph.edges[edge],
        )
    return graph_4d
