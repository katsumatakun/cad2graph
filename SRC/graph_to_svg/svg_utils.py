def draw_line(line):

    return line.svg(stroke_color='rgb({r},{g},{b})')


def draw_edge(
        edge,
        grid_size,
        color="rgb(0,0,255)",
):     
    return f"<line stroke='{color}' stroke-width='5'" \
           f" x1='{(edge[0].x+0.5)*grid_size}' x2='{(edge[1].x+0.5)*grid_size}'" \
           f" y1='{(edge[0].y+0.5)*grid_size}' y2='{(edge[1].y+0.5)*grid_size}' />"


def draw_block(x, y, grid_size, color):
    opacity = "0.3"

    square_line = f'<rect x="{x*grid_size}" y="{y*grid_size}" width="{grid_size}" height="{grid_size}" '
    square_line += f'style="fill:{color};stroke:pink;stroke-width:1;fill-opacity:{opacity};'
    square_line += 'stroke-opacity:0.9" />'

    return square_line


def draw_circle(x, y, grid_size, color):
    opacity = "0.3"
    
    square_line = f'<circle cx="{(x+0.5)*grid_size}" cy="{(y+0.5)*grid_size}" r="{grid_size*1.5}" '
    # square_line = f'<circle cx="{(x+.5)*grid_size}" cy="{(y+.5)*grid_size}" r="{grid_size*0.5}" '
    square_line += f'style="fill:{color};stroke:pink;stroke-width:10;fill-opacity:{opacity};'
    square_line += 'stroke-opacity:0.9" />'

    return square_line


def write_text(x, y, grid_size, text):

    return f'<text font-size="8" x="{x*grid_size}" y="{(y-1)*grid_size}" fill="black">{text}</text>'
