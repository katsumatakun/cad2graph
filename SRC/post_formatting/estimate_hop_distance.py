import csv
from networkx import read_yaml
from networkx import compose_all
from collections import defaultdict
from typing import List
from graph.graph_utils import compute_hospital_graph_shortest_path


def compare_hop_distances(
        db_roomnames_filepath: str,
):
    graph_filepaths = [
        ("data/graphs2/GeneralHospital.yaml","GH"),
        # ("/Users/talalriaz/RA_FALL_2017/dxf_to_graph/data/graphs/GeneralHospital.yaml","GH"),
        # ("/Users/talalriaz/RA_FALL_2017/dxf_to_graph/data/graphs/JohnColloton.yaml","JCP"),
        # ("/Users/talalriaz/RA_FALL_2017/dxf_to_graph/data/graphs/BoydTower.yaml","BT"),
        # ("/Users/talalriaz/RA_FALL_2017/dxf_to_graph/data/graphs/JohnPappajohn.yaml","JPP"),
        # ("/Users/talalriaz/RA_FALL_2017/dxf_to_graph/data/graphs/RoyCarver.yaml","RCP"),
    ]
    graphs = {}
    for graph_name in graph_filepaths:
        graphs[graph_name[1]] = read_yaml(graph_name[0])
    z = 0
    y=0
    hop_distances = []
    with open(db_roomnames_filepath) as db_rooms_file:
        dic_reader = csv.DictReader(db_rooms_file, delimiter="\t")
        for row in dic_reader:
            z += 1
            hops_manual = int(row["dist"])
            if row["building1"] not in graphs:
                continue
            try:
                hops_graph = compute_hospital_graph_shortest_path(
                    hospital_graph=graphs[row["building1"]],
                    room_label_1=row["room1"].split(".")[-1],
                    room_label_2=row["room2"].split(".")[-1],
                )
                if hops_graph:
                    hop_distances.append(
                        (
                            hops_graph,
                            hops_manual,
                            row["room1"],
                            row["room2"],
                            row["building1"],
                            row["building2"],
                            row["desc1"],
                            row["desc2"],
                        ),
                    )
                    y += 1
                    if y%100 == 0:
                        print(y)
            except:
                continue


    with open("final_hops_data.csv", "w+") as outfile:
        for i in hop_distances:
            outfile.write(str(i)[1:-1]+"\n")


compare_hop_distances("/Users/talalriaz/RA_FALL_2017/dxf_to_graph/out2.txt")
