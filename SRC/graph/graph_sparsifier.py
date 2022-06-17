import logging
from typing import Set

from networkx import Graph
from networkx import connected_component_subgraphs
from networkx import single_source_shortest_path

from graph.graph_utils import compute_neighborhood_cached
from graph.graph_utils import is_neighborhood_marked
from graph.graph_utils import shortest_path_less_than_cutoff
from util.data_containers import Node
from util.data_containers import Point


def sparsify_graph(
        graph: Graph,
        sparsity_level: int,
) -> Graph:
    """This function sparsifies a graph according to a given sparsity level.
    The sparsity level shows the minimum distance between two nodes in the
    sparsified graph that is desired.

    :param graph: A networkx graph that must be sparsified.
    :param sparsity_level: Minimum distance in 'graph' between any two nodes
           in the sparsified graph.
    :return: A networkx graph that has been sparsified.
    """
    sparsified_graph = Graph()
    sparsify_add_nodes_with_labels(graph, sparsified_graph)
    sparsify_add_rooms(graph, sparsified_graph, sparsity_level)
    sparsify_add_nodes(graph, sparsified_graph, sparsity_level)
    sparsify_add_edges(graph, sparsified_graph, cutoff=int(1.5 * sparsity_level))
    add_distance_reducing_edges(graph, sparsified_graph, cutoff=int(1.8*sparsity_level))
    add_distance_reducing_edges(graph, sparsified_graph, cutoff=int(2*sparsity_level+1))
    join_components(graph, sparsified_graph, sparsity_level)

    return sparsified_graph


def _subroutine_add_edge(
        graph: Graph,
        sparsified_graph,
        source: Node,
        dest: Node,
        cutoff: int,
) -> None:
    """A subroutine to add an edge to the sparsified graph that is repeatedly
    used. It adds a door or

    :param graph: A networkx graph that must be sparsified.
    :param sparsified_graph: A sparsified networkx graph which doesn't have
           sufficient edges.
    :param source: The candidate source node for an edge.
    :param dest: The candidate dest node for an edge.
    :param cutoff: The minimum
    :return:
    """
    door_nhood = compute_neighborhood_cached(
        G=graph,
        source=source,
        cutoff=cutoff,
        weight="weight2",
    )
    if dest not in door_nhood:
        sparsified_graph.add_edge(
            source,
            dest,
            weight2=1000,
            type="door",
        )
    else:
        sparsified_graph.add_edge(
            source,
            dest,
            weight2=1,
            type="normal",
        )


def join_components(
        graph: Graph,
        sparsified_graph: Graph,
        sparsity_level: int,
):
    """Joins disjoint graph components from the sparsified graph if they are
    close in graph.

    :param graph: The graph to search for distances in.
    :param sparsified_graph: The sparsified graph with disjoint components.
    :param sparsity_level: Join nodes from the disjoint components that are
           closer than 2*sparsity_level+1
    :return:
    """
    components = connected_component_subgraphs(sparsified_graph)
    edges_to_add = []
    for component in components:
        for node in component.nodes:
            nhood = compute_neighborhood_cached(
                G=graph,
                source=node,
                cutoff=2*sparsity_level+1,
            )
            for neighbor in nhood:
                if neighbor not in component.nodes:
                    if neighbor in sparsified_graph.nodes:
                        edges_to_add.append([node, neighbor])

    for edge in edges_to_add:
        sparsified_graph.add_edge(edge[0], edge[1])


def sparsify_add_nodes(
        graph: Graph,
        sparsified_graph: Graph,
        sparsity_level: int,
):
    """Adds any node u from graph to the sparsified graph if it can't find
    any node within distance sparsity_level of u in graph, in sparisified_graph

    :param graph: the graph to search distances in.
    :param sparsified_graph: the sparsified_graph
    :param sparsity_level: the distance threshold.
    :return:
    """
    all_nodes = list(graph.nodes)
    i = 0
    percent_done = 0
    j = 0
    for node in graph.nodes:
        i += 1
        if int(i/len(all_nodes)*100) != percent_done:
            percent_done = int(i/len(all_nodes)*100)
            logging.debug(f"SPARSIFYING add nodes: {percent_done}% done")
        nhood = compute_neighborhood_cached(
            G=graph,
            source=node,
            cutoff=sparsity_level,
        )
        if not is_neighborhood_marked(sparsified_graph, nhood):
            j += 1
            sparsified_graph.add_node(
                node,
                **graph.nodes[node],
            )
    logging.info(f"{j} nodes added")


def sparsify_add_nodes_with_labels(
        graph: Graph,
        sparsified_graph:  Graph,
):
    """We add all nodes with labels in graph to sparsified_graph. These labels
    are normally associated with room centers so this is a good strategy.

    :param graph: The unsparsified graph which has a grid representation of space
           in the CAD file.
    :param sparsified_graph: A sparsified representation of `graph` which only has
           nodes but no edges.
    :return:
    """
    for node in graph.nodes:
        if graph.nodes[node]["room_label"]:
            sparsified_graph.add_node(
                node,
                **graph.nodes[node],
            )


def sparsify_add_rooms(
        graph: Graph,
        sparsified_graph: Graph,
        sparsity_level: int,
):
    """Adds nodes centrally located in a sufficiently sized empty space in
    graph to sparsified_graph. Our intution is that these should capture rooms
    and allow for nodes to be spaced away from walls.

    :param graph: The unsparsified graph which has a grid representation of space
           in the CAD file.
    :param sparsified_graph: A sparsified representation of `graph` which only has
           nodes but no edges.
    :param sparsity_level: The cutoff for distance in `graph` which will be used to
           connect nodes in sparsified graph.
    :return:
    """
    all_nodes = list(graph.nodes)
    i = 0
    percent_done = 0
    count = 0
    for node in graph.nodes:
        i += 1
        if int(i/len(all_nodes)*100) != percent_done:
            percent_done = int(i/len(all_nodes)*100)
            logging.debug(f"SPARSIFYING add rooms: {percent_done}% done")

        is_nhood_intact = True
        for j in [1, 2, 3]:
            i_nhood = single_source_shortest_path(
                G=graph,
                source=node,
                cutoff=j,
            )
            if len(i_nhood) < (2*j + 1)**2 - 1:
                is_nhood_intact = False

        if is_nhood_intact:
            nhood = compute_neighborhood_cached(
                G=graph,
                source=node,
                cutoff=sparsity_level,
            )
            if not is_neighborhood_marked(sparsified_graph, nhood):
                count += 1
                sparsified_graph.add_node(
                    node,
                    **graph.nodes[node],
                )
    logging.info(f"{count} rooms added")


def sparsify_add_edges(
        graph: Graph,
        sparsified_graph: Graph,
        cutoff: int,
):
    """Adds edges between nodes in `sparsified_graph` based on distance
    in `graph`.

    :param graph: The unsparsified graph which has a grid representation of space
           in the CAD file.
    :param sparsified_graph: A sparsified representation of `graph` which only has
           nodes but no edges.
    :param cutoff: The cutoff for distance in `graph` which will be used to connect
           nodes in sparsified graph.
    :return:
    """
    # sparse_nodes = set(sparsified_graph.nodes)
    for node in sparsified_graph.nodes:
        nhood = compute_neighborhood_cached(
            G=graph,
            source=node,
            cutoff=cutoff,
        )
        door_nhood = compute_neighborhood_cached(
            G=graph,
            source=node,
            cutoff=cutoff,
            weight="weight2",
        )

        for neighbor in nhood:
            if neighbor in sparsified_graph.nodes:
                is_door = neighbor not in door_nhood ### changed from is_door = neighbor not in door_nhood
                sparsified_graph.add_edge(
                    node,
                    neighbor,
                    weight2=1000 if is_door else 1,
                    type="door" if is_door else "normal",
                )


def add_distance_reducing_edges(
        graph: Graph,
        sparsified_graph: Graph,
        cutoff: int,
):
    """

    :param graph:
    :param sparsified_graph:
    :param cutoff:
    :return:
    """
    for node in sparsified_graph.nodes:
        grid_nhood = compute_neighborhood_cached(
            G=graph,
            source=node,
            cutoff=cutoff,
        )
        door_nhood = compute_neighborhood_cached(
            G=graph,
            source=node,
            cutoff=cutoff,
            weight="weight2",
        )
        for neighbor in grid_nhood:
            if neighbor in sparsified_graph.nodes:
                if not shortest_path_less_than_cutoff(
                    graph=sparsified_graph,
                    source=node,
                    target=neighbor,
                    cutoff=3,
                ):
                    is_door = neighbor not in door_nhood
                    sparsified_graph.add_edge(
                        node,
                        neighbor,
                        weight2=1000 if is_door else 1,
                        type="door" if is_door else "normal",
                    )

    logging.info("distance reducing edges added")


def get_room_label(
        nhood: Set[Point],
        graph: Graph,
):
    for node in nhood:
        if graph.nodes[node]["room_label"]:
            return graph.nodes[node]["room_label"]
    return None


def remove_small_components(graph: Graph, minsize):
    updated_graph = Graph()
    components = connected_component_subgraphs(graph)

    for component in components:
        if component.number_of_nodes() > minsize:
            updated_graph.add_nodes_from(component.nodes(data=True))
            updated_graph.add_edges_from(component.edges(data=True))
    return updated_graph
    # return max(connected_component_subgraphs(graph), key=len)

def remove_components_without_labels(graph: Graph):
    updated_graph = Graph()
    components = connected_component_subgraphs(graph)
    
    for component in components:
        label_exist = False
        for node in component.nodes:
            if component.nodes[node]["room_label"]:
                label_exist = True
        if label_exist:
            updated_graph.add_nodes_from(component.nodes(data=True))
            updated_graph.add_edges_from(component.edges(data=True))
        else:
            print("removed")
        
    return updated_graph
    
