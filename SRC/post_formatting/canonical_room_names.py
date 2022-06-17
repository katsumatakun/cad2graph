import csv
from networkx import read_yaml


def add_canonical_room_names(
        db_roomnames_filepath: str,
        graph_filepath: str,
):
    graph = read_yaml(graph_filepath)
    rooms_to_ids = {}
    with open(db_roomnames_filepath) as db_rooms_file:
        dic_reader = csv.DictReader(db_rooms_file, delimiter="\t")
        for row in dic_reader:
            rooms_to_ids[row["room"]] = row["rid"]
    rooms_found = []
    hyphen_rooms_found = []
    rooms_not_found = []
    extensions_dropped_found = []

    aaa = {}
    for i in rooms_to_ids:
        t = get_transformed_roomname(i)
        aaa[t] = 1

    print(len(aaa.keys()))
    a = {}
    for node in graph.nodes:
        if "dx" not in graph.nodes[node]["room_label"]:
            label = graph.nodes[node]["room_label"]
            a[label] = 1

    print(len(a.keys()))

    for room_name in aaa:
        transformed_roomname = get_transformed_roomname(room_name)
        if graph_has_room_label(graph, transformed_roomname, transform=lambda x: x):
            rooms_found.append(room_name)
        elif graph_has_room_label(graph, transformed_roomname, transform=remove_hyphens):
            hyphen_rooms_found.append(room_name)
        elif graph_has_room_label(graph, transformed_roomname, transform=drop_extensions):
            extensions_dropped_found.append(room_name)
        else:
            rooms_not_found.append(room_name)

    rooms_not_found = remove_derived_rooms(rooms_not_found)

    print("rooms_found", len(rooms_found))
    print("hyphen_rooms_found", len(hyphen_rooms_found))
    print("extensions_dropped_found", len(extensions_dropped_found))
    print("rooms_not_found", len(rooms_not_found))
    print("Match %", len(rooms_not_found) / (len(rooms_found) + len(hyphen_rooms_found) + len(extensions_dropped_found)))

    return rooms_found, hyphen_rooms_found, extensions_dropped_found, rooms_not_found


def get_transformed_roomname(roomname: str) -> str:
    transformed_roomname = roomname.split(".")[-1]
    transformed_roomname = transformed_roomname.split("$")[0]
    return transformed_roomname


def graph_has_room_label(graph, room_label, transform):
    for node in graph.nodes:
        if transform(graph.nodes[node]["room_label"]) == transform(room_label):
            return True
    return False


def remove_hyphens(word: str) -> str:
    word = word.split("-")
    return "".join(word)


def remove_derived_rooms(rooms_list):
    a = {}
    for room in rooms_list:
        room = room.split("$")[0]
        a[room] = 1
    return list(a.keys())


def drop_extensions(word: str) -> str:
    return word.split("-")[0]
