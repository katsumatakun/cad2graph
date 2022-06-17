from dxf_reader.hospital_dxf import DXF
from graph_to_svg.svg_utils import draw_edge, draw_circle, write_text
from util.data_containers import SpaceType


def export_graph_overlay_on_cad(dxf: DXF, graph, grid_size, canvas_lims, outfile):
    with open(outfile, "w+") as dwg:
        header = "<?xml version='1.0' encoding='utf-8' ?> <svg baseProfile='tiny' \n"
        header += f"height='{canvas_lims[1]}' version='1.1' width='{canvas_lims[0]}' xmlns='http://www.w3.org/2000/svg' \n"
        header += "xmlns:ev='http://www.w3.org/2001/xml-events' xmlns:xlink='http://www.w3.org/1999/xlink'><defs />"
        dwg.write(header)

        for wall in dxf.walls:
            dwg.write(wall.svg())
            dwg.write("\n")

        for door in dxf.doors:
            dwg.write(door.svg())
            dwg.write("\n")
        print("draw node")
        for node in graph.nodes:
            if graph.nodes[node]["type"] == SpaceType.OPEN:
                dwg.write(draw_circle(node.x, node.y, grid_size, "rgb(0,0,0)"))
            elif graph.nodes[node]["type"] == SpaceType.DOOR:
                dwg.write(draw_circle(node.x, node.y, grid_size, "rgb(255,0,0)"))
            else:
                dwg.write(draw_circle(node.x, node.y, grid_size, "rgb(0,0,0)"))
                
            label = graph.nodes[node].get("room_label") or 'NA'
            dwg.write(
                write_text(
                    x=node.x,
                    y=node.y,
                    grid_size=grid_size,
                    text=f'{label}+{node.x}+{node.y}',
                ),
            )

            dwg.write("\n")

        for edge in graph.edges:
            if "type" not in graph.edges[edge]:
                dwg.write(draw_edge(edge, grid_size, color="rgb(153,0,0)"))
            elif graph.edges[edge]["type"] == "door":
                dwg.write(draw_edge(edge, grid_size, color="rgb(153,76,0)"))
            else:
                dwg.write(draw_edge(edge, grid_size))
                # dwg.write(draw_edge(edge, 20))
            dwg.write("\n")

        dwg.write("</svg>")


def export_dxf_as_svg(dxf: DXF, outfile):
    canvas_lims = dxf.new_canvas_dimensions
    with open(outfile, "w+") as dwg:
        header = "<?xml version='1.0' encoding='utf-8' ?> <svg baseProfile='tiny' \n"
        header += f"height='{canvas_lims[1]}' version='1.1' width='{canvas_lims[0]}' xmlns='http://www.w3.org/2000/svg' \n"
        header += "xmlns:ev='http://www.w3.org/2001/xml-events' xmlns:xlink='http://www.w3.org/1999/xlink'><defs />"
        dwg.write(header)

        for wall in dxf.walls:
            dwg.write(wall.svg())
            dwg.write("\n")

        for door in dxf.doors:
            dwg.write(door.svg(stroke_color='rgb(255,0,255)'))
            dwg.write("\n")

        dwg.write("</svg>")
