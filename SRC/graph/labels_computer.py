import logging

from networkx import Graph

from graph.graph_utils import compute_neighborhood_cached


def propagate_labels(
        sparsified_graph: Graph,
):
    logging.info("Propagating Labels")
    labelled_nodes = set()
    for node in sparsified_graph.nodes:
        if sparsified_graph.nodes[node]["room_label"]:
            labelled_nodes.add(node)
            
    print("len labeled node", len(labelled_nodes))

    for node in labelled_nodes:
        for cutoff in range(1, 6):
            nhood = compute_neighborhood_cached(
                G=sparsified_graph,
                source=node,
                cutoff=cutoff,
                weight="weight2",
            )
            for neighbor in nhood:
                if not sparsified_graph.nodes[neighbor]["room_label"]:
                    sparsified_graph.nodes[neighbor]["room_label"] = \
                        f'{sparsified_graph.nodes[node]["room_label"]}~~'
