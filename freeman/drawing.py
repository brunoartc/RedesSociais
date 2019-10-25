"""Module responsible for rendering graph visualizations.

The visualizations are powered by two different libraries, `pyvis
<https://pyvis.readthedocs.io/en/latest/>`_ and `Plotly
<https://plot.ly/python/>`_, but they are configured to be as *consistent* as
possible across these libraries.

The functions and classes require nodes to be *positioned*: given a graph **g**
and a node **n** of this graph, the attribute **g.nodes[n]['pos']** must be a
tuple or list of two numbers between ``0`` and ``1``. To ensure these
attributes, use the functions from the :ref:`Moving <moving>` module or wrap
with the :func:`Graph <freeman.Graph>` class.

The appearance is based on the eighteen visual attributes below.


.. _visual-attributes:

Visual attributes
-----------------

Given a graph **g**, the six attributes below can be used for customizing the
appearance of this graph. When the attribute does not exist, its default value
is considered.

=====================  =
**g.graph['width']**   Graph width, in pixels. Must be positive. Default value is ``800``.

**g.graph['height']**  Graph height, in pixels. Must be positive. Default value is ``450``.

**g.graph['bottom']**  Bottom padding, in pixels. Must be non-negative. Default value is ``0``.

**g.graph['left']**    Left padding, in pixels. Must be non-negative. Default value is ``0``.

**g.graph['right']**   Right padding, in pixels. Must be non-negative. Default value is ``0``.

**g.graph['top']**     Top padding, in pixels. Must be non-negative. Default value is ``0``.
=====================  =

Given a graph **g** and a node **n** of this graph, the six attributes below can
be used for customizing the appearance of this node. When the attribute does not
exist, its default value is considered.

========================  =
**g.nodes[n]['size']**    Node size, in pixels. Must be positive. Default value is ``20``.

**g.nodes[n]['style']**   Node style, one of: ``'circle'``, ``'star'``, ``'square'``,
                          ``'diamond'``, ``'triangle-up'``, or ``'triangle-down'``. Default
                          value is ``'circle'``.

**g.nodes[n]['color']**   Node color, as a tuple or list of three integers between ``0`` and
                          ``255`` representing red, green, and blue levels, respectively.
                          Default value is ``(255, 255, 255)``.

**g.nodes[n]['bwidth']**  Node border width, in pixels. Must be non-negative. Default value is
                          ``1``.

**g.nodes[n]['bcolor']**  Node border color, as a tuple or list of three integers between ``0``
                          and ``255`` representing red, green, and blue levels, respectively.
                          Default value is ``(0, 0, 0)``.

**g.nodes[n]['labpos']**  Node label position, either ``'hover'`` or ``'<vpos> <hpos>'``, where
                          ``<vpos>`` is ``bottom``, ``middle``, or ``top``, and ``<hpos>`` is
                          ``left``, ``center``, or ``right``. Default value is ``'middle
                          center'``.
========================  =

Given a graph **g** and an edge **(n, m)** of this graph, the six attributes
below can be used for customizing the appearance of this edge. When the
attribute does not exist, its default value is considered.

============================  =
**g.edges[n, m]['width']**    Edge width, in pixels. Must be positive. Default value is ``1``.

**g.edges[n, m]['style']**    Edge style, one of ``'solid'``, ``'dash'``, ``'dot'``, or
                              ``'dashdot'``. Default value is ``'solid'``.

**g.edges[n, m]['color']**    Edge color, as a tuple or list of three integers between ``0``
                              and ``255`` representing red, green, and blue levels,
                              respectively, and an optional number between ``0`` and ``1``
                              representing opacity. Default value is ``(0, 0, 0)``.

**g.edges[n, m]['labflip']**  Whether the label should be positioned to the right of the edge
                              instead of the left. Default value is ``False``.

**g.edges[n, m]['labdist']**  Distance from edge to label, in pixels. Must be non-negative.
                              Default value is ``10``.

**g.edges[n, m]['labfrac']**  Where the label should be positioned between the two nodes. The
                              closer the value is to ``0``, the closer the label is to the
                              source. The closer the value is to ``1``, the closer the label is
                              to the target. Default value is ``0.5``.
============================  =
"""
import os
import plotly

import networkx as nx

from warnings import warn
from math import isclose, sqrt, cos, sin
from IPython.display import display
from pyvis.network import Network


CACHE_DIR = '__fmcache__'

NODE_STYLES = {
    'circle': 'dot',
    'star': 'star',
    'square': 'square',
    'diamond': 'diamond',
    'triangle-up': 'triangle',
    'triangle-down': 'triangleDown',
}

EDGE_SCALE = 0.4
EDGE_SPACE = 5
EDGE_SIZE = 10
EDGE_ANGLE = 0.3

EDGE_STYLES = {
    'solid': False,
    'dash': [10, 8],
    'dot': [3, 3],
    'dashdot': [10, 3, 2, 3],
}


graph_width = 800
graph_height = 450
graph_bottom = 0
graph_left = 0
graph_right = 0
graph_top = 0

node_size = 20
node_style = 'circle'
node_color = (255, 255, 255)
node_bwidth = 1
node_bcolor = (0, 0, 0)
node_labpos = 'middle center'

edge_width = 1
edge_style = 'solid'
edge_color = (0, 0, 0)
edge_labflip = False
edge_labdist = 10
edge_labfrac = 0.5


def _scale(dx, dy, width, height, size):
    d2 = (dx * width)**2 + (dy * height)**2

    if isclose(d2, 0):
        return dx, dy

    s = sqrt(size**2 / d2)

    return s * dx, s * dy


def _rotate(dx, dy, width, height, angle):
    dx *= width
    dy *= height

    rx = dx * cos(angle) - dy * sin(angle)
    ry = dx * sin(angle) + dy * cos(angle)

    return rx / width, ry / height


def _correct(c):
    sc = c / 255

    if sc > 0.03928:
        return ((sc + 0.055) / 1.055)**2.4

    return sc / 12.92


def _convert(color):
    r = color[0]
    g = color[1]
    b = color[2]

    if len(color) == 4:
        a = color[3]

        return 'rgba({}, {}, {}, {})'.format(r, g, b, a)

    return 'rgb({}, {}, {})'.format(r, g, b)


def _build_graph_width(g):
    width = g.graph.get('width', graph_width)
    if not isinstance(width, int):
        raise TypeError('graph width must be an integer')
    if width <= 0:
        raise ValueError('graph width must be positive')

    return width


def _build_graph_height(g):
    height = g.graph.get('height', graph_height)
    if not isinstance(height, int):
        raise TypeError('graph height must be an integer')
    if height <= 0:
        raise ValueError('graph height must be positive')

    return height


def _build_graph_padding(g):
    bottom = g.graph.get('bottom', graph_bottom)
    if not isinstance(bottom, int):
        raise TypeError('graph bottom must be an integer')
    if bottom < 0:
        raise ValueError('graph bottom must be non-negative')

    left = g.graph.get('left', graph_left)
    if not isinstance(left, int):
        raise TypeError('graph left must be an integer')
    if left < 0:
        raise ValueError('graph left must be non-negative')

    right = g.graph.get('right', graph_right)
    if not isinstance(right, int):
        raise TypeError('graph right must be an integer')
    if right < 0:
        raise ValueError('graph right must be non-negative')

    top = g.graph.get('top', graph_top)
    if not isinstance(top, int):
        raise TypeError('graph top must be an integer')
    if top < 0:
        raise ValueError('graph top must be non-negative')

    return bottom, left, right, top


def _build_graph_key(g):
    width = _build_graph_width(g)
    height = _build_graph_height(g)

    bottom, left, right, top = _build_graph_padding(g)

    return width, height, bottom, left, right, top


def _get_node_pos(g, n):
    if 'pos' not in g.nodes[n]:
        raise KeyError('node must have a pos')
    pos = g.nodes[n]['pos']
    if not isinstance(pos, (tuple, list)):
        raise TypeError('node pos must be a tuple or list')
    if len(pos) != 2:
        raise ValueError('node pos must have exactly two elements')
    if not isinstance(pos[0], (int, float)) or not isinstance(pos[1], (int, float)):
        raise TypeError('both node pos elements must be numeric')
    if pos[0] < 0 or pos[0] > 1 or pos[1] < 0 or pos[1] > 1:
        raise ValueError('both node pos elements must be between 0 and 1')

    return pos


def _build_node_size(g, n):
    size = g.nodes[n].get('size', node_size)
    if not isinstance(size, int):
        raise TypeError('node size must be an integer')
    if size <= 0:
        raise ValueError('node size must be positive')

    return size


def _build_node_key(g, n):
    size = _build_node_size(g, n)

    style = g.nodes[n].get('style', node_style)
    if style not in NODE_STYLES:
        raise KeyError('node style must be one of the following: ' + ', '.join('"{}"'.format(s) for s in NODE_STYLES))

    color = g.nodes[n].get('color', node_color)
    if not isinstance(color, (tuple, list)):
        raise TypeError('node color must be a tuple or list')
    if len(color) != 3:
        raise ValueError('node color must have exactly three elements')
    if not isinstance(color[0], int) or not isinstance(color[1], int) or not isinstance(color[2], int):
        raise TypeError('all node color elements must be integers')
    if color[0] < 0 or color[0] > 255 or color[1] < 0 or color[1] > 255 or color[2] < 0 or color[2] > 255:
        raise ValueError('all node color elements must be between 0 and 255')

    bwidth = g.nodes[n].get('bwidth', node_bwidth)
    if not isinstance(bwidth, int):
        raise TypeError('node bwidth must be an integer')
    if bwidth < 0:
        raise ValueError('node bwidth must be non-negative')

    bcolor = g.nodes[n].get('bcolor', node_bcolor)
    if not isinstance(bcolor, (tuple, list)):
        raise TypeError('node bcolor must be a tuple or list')
    if len(bcolor) != 3:
        raise ValueError('node bcolor must have exactly three elements')
    if not isinstance(bcolor[0], int) or not isinstance(bcolor[1], int) or not isinstance(bcolor[2], int):
        raise TypeError('all node ncolor elements must be integers')
    if bcolor[0] < 0 or bcolor[0] > 255 or bcolor[1] < 0 or bcolor[1] > 255 or bcolor[2] < 0 or bcolor[2] > 255:
        raise ValueError('all node ncolor elements must be between 0 and 255')

    labpos = g.nodes[n].get('labpos', node_labpos)
    if not isinstance(labpos, str):
        raise TypeError('node labpos must be a string')
    if labpos != 'hover':
        words = labpos.split(' ')
        if len(words) != 2:
            raise ValueError('node labpos must be "hover" or a vertical position and an horizontal position separated by a space')
        vpos = ['bottom', 'middle', 'top']
        if words[0] not in vpos:
            raise KeyError('node vertical position must be one of the following: ' + ', '.join('"{}"'.format(v) for v in vpos))
        hpos = ['left', 'center', 'right']
        if words[1] not in hpos:
            raise KeyError('node horizontal position must be one of the following: ' + ', '.join('"{}"'.format(h) for h in hpos))

    return size, style, color, bwidth, bcolor, labpos


def _build_edge_key(g, n, m):
    n_size = _build_node_size(g, n)
    m_size = _build_node_size(g, m)

    width = g.edges[n, m].get('width', edge_width)
    if not isinstance(width, int):
        raise TypeError('edge width must be an integer')
    if width <= 0:
        raise ValueError('edge width must be positive')

    style = g.edges[n, m].get('style', edge_style)
    if style not in EDGE_STYLES:
        raise KeyError('edge style must be one of the following: ' + ', '.join('"{}"'.format(s) for s in EDGE_STYLES))

    color = g.edges[n, m].get('color', edge_color)
    if not isinstance(color, (tuple, list)):
        raise TypeError('edge color must be a tuple or list')
    if len(color) != 3 and len(color) != 4:
        raise ValueError('edge color must have three or four elements')
    if not isinstance(color[0], int) or not isinstance(color[1], int) or not isinstance(color[2], int):
        raise TypeError('the first three edge color elements must be integers')
    if color[0] < 0 or color[0] > 255 or color[1] < 0 or color[1] > 255 or color[2] < 0 or color[2] > 255:
        raise ValueError('the first three edge color elements must be between 0 and 255')
    if len(color) == 4 and not isinstance(color[3], (int, float)):
        raise TypeError('the fourth edge color element must be numeric')
    if len(color) == 4 and (color[3] < 0 or color[3] > 1):
        raise ValueError('the fourth edge color element must be between 0 and 1')

    labflip = g.edges[n, m].get('labflip', edge_labflip)
    if not isinstance(labflip, bool):
        raise TypeError('edge labflip must be a boolean')

    labdist = g.edges[n, m].get('labdist', edge_labdist)
    if not isinstance(labdist, int):
        raise TypeError('edge labdist must be an integer')
    if labdist < 0:
        raise ValueError('edge labdist must be non-negative')

    labfrac = g.edges[n, m].get('labfrac', edge_labfrac)
    if not isinstance(labfrac, (int, float)):
        raise TypeError('edge labfrac must be numeric')
    if labfrac < 0 or labfrac > 1:
        raise ValueError('edge labfrac must be between 0 and 1')

    return n_size, m_size, width, style, color, labflip, labdist, labfrac


def _build_node_trace(size, style, color, bwidth, bcolor, labpos):
    if labpos == 'hover':
        hoverinfo = 'text'
        mode = 'markers'
        textposition = 'middle center'
    else:
        hoverinfo = 'none'
        mode = 'markers+text'
        textposition = labpos

    textcolor = (0, 0, 0)

    if labpos == 'middle center':
        r = _correct(color[0])
        g = _correct(color[1])
        b = _correct(color[2])

        if (0.2126 * r + 0.7152 * g + 0.0722 * b + 0.05)**2 < 0.0525:
            textcolor = (255, 255, 255)

    return {
        'x': [],
        'y': [],
        'text': [],
        'hoverinfo': hoverinfo,
        'mode': mode,
        'marker': {
            'size': size,
            'symbol': style,
            'color': _convert(color),
            'line': {
                'width': bwidth,
                'color': _convert(bcolor),
            },
        },
        'textposition': textposition,
        'textfont': {
            'color': _convert(textcolor),
        },
    }


def _build_node_label_trace(width, height, bottom, left, right, top):
    return {
        'x': [0.5, -left / width, 1 + right / width, 0.5],
        'y': [-bottom / height, 0.5, 0.5, 1 + top / height],
        'hoverinfo': 'none',
        'mode': 'markers',
        'marker': {
            'size': 0,
            'symbol': 'circle',
            'color': 'rgba(255, 255, 255, 0.0)',
            'line': {
                'width': 0,
                'color': 'rgba(255, 255, 255, 0.0)',
            },
        },
    }


def _build_edge_trace(width, style, color):
    return {
        'x': [],
        'y': [],
        'hoverinfo': 'none',
        'mode': 'lines',
        'line': {
            'width': width,
            'dash': style,
            'color': _convert(color),
        },
    }


def _build_edge_label_trace():
    return {
        'x': [],
        'y': [],
        'text': [],
        'hoverinfo': 'none',
        'mode': 'text',
        'textposition': 'middle center',
        'textfont': {
            'color': 'rgb(0, 0, 0)',
        },
    }


def _build_layout(width, height):
    return {
        'showlegend': False,
        'width': width,
        'height': height,
        'margin': {
            'b': 0,
            'l': 0,
            'r': 0,
            't': 0,
        },
        'xaxis': {
            'showgrid': False,
            'zeroline': False,
            'showticklabels': False,
        },
        'yaxis': {
            'showgrid': False,
            'zeroline': False,
            'showticklabels': False,
        },
    }


def _add_node(g, n, node_trace):
    x, y = _get_node_pos(g, n)
    text = g.nodes[n].get('label', None)

    node_trace['x'].append(x)
    node_trace['y'].append(y)
    node_trace['text'].append(text)


def _add_edge(g, n, m, edge_trace, edge_label_trace, width, height, n_size, m_size, labflip, labdist, labfrac):
    x0, y0 = _get_node_pos(g, n)
    x1, y1 = _get_node_pos(g, m)

    # parameters estimated from screenshots
    width = 0.9 * width - 24
    height = 0.9 * height - 24

    ratio = width / height
    dx = (y0 - y1) / ratio
    dy = (x1 - x0) * ratio

    if isinstance(g, nx.DiGraph) and g.has_edge(m, n):
        edge_space = max(0, min(EDGE_SPACE, n_size - 2, m_size - 2))
        sx, sy = _scale(dx, dy, width, height, edge_space / 2)
        x0 += sx
        y0 += sy
        x1 += sx
        y1 += sy

    edge_trace['x'].extend([x0, x1, None])
    edge_trace['y'].extend([y0, y1, None])

    if labflip:
        dx = -dx
        dy = -dy
    sx, sy = _scale(dx, dy, width, height, labdist)
    edge_label_trace['x'].append(x0 + labfrac * (x1 - x0) + sx)
    edge_label_trace['y'].append(y0 + labfrac * (y1 - y0) + sy)
    edge_label_trace['text'].append(g.edges[n, m].get('label', None))

    if isinstance(g, nx.DiGraph):
        dx = x0 - x1
        dy = y0 - y1

        radius = m_size / 2
        sx, sy = _scale(dx, dy, width, height, radius)
        x0 = x1 + sx
        y0 = y1 + sy
        edge_size = max(1, min(EDGE_SIZE, radius))
        sx, sy = _scale(dx, dy, width, height, edge_size)

        rx, ry = _rotate(sx, sy, width, height, -EDGE_ANGLE)
        x1 = x0 + rx
        y1 = y0 + ry
        edge_trace['x'].extend([x0, x1, None])
        edge_trace['y'].extend([y0, y1, None])

        if not g.has_edge(m, n):
            rx, ry = _rotate(sx, sy, width, height, EDGE_ANGLE)
            x1 = x0 + rx
            y1 = y0 + ry
            edge_trace['x'].extend([x0, x1, None])
            edge_trace['y'].extend([y0, y1, None])


def interact(g, path=None, physics=False):
    """Render an interactive visualization of a graph.

    The visualization is powered by `pyvis
    <https://pyvis.readthedocs.io/en/latest/>`_, based on the :ref:`visual
    attributes <visual-attributes>`, and mostly consistent with the :func:`draw
    <freeman.drawing.draw>` function and the :func:`Animation
    <freeman.drawing.Animation>` class. The only significative difference is
    that a pair of edges **(n, m)** and **(m, n)** in a directed graph is
    rendered as a single edge with two heads. Such rendering is better for
    interaction, but less faithful to the graph density.

    The visualization must be saved to an HTML file.

    :type g: NetworkX Graph or DiGraph
    :param g: The graph to visualize.

    :type path: str
    :param path: Path of the HTML file. If ``None``, the visualization is saved to
                 ``'__fmcache__/<id>.html'``, where ``<id>`` is the `identity
                 <https://docs.python.org/3/library/functions.html#id>`_ of the graph.

    :type physics: bool
    :param physics: Whether to enable the physics simulation.
    """
    local_width, local_height, local_bottom, local_left, local_right, local_top = _build_graph_key(g)
    dx = local_left + local_right
    dy = local_bottom + local_top
    network = Network(
        height=local_height + dy,
        width=local_width + dx,
        directed=isinstance(g, nx.DiGraph),
        notebook=True,
        bgcolor='#ffffff',
        font_color='#000000',
        layout=None,
    )

    dx = local_left - dx // 2
    dy = local_top - dy // 2
    for n in g.nodes:
        x, y = _get_node_pos(g, n)
        size, style, color, bwidth, bcolor, _ = _build_node_key(g, n)
        color = _convert(color)
        bcolor = _convert(bcolor)
        options = {
            'borderWidth': bwidth,
            'borderWidthSelected': 1,
            'color': {
                'border': bcolor,
                'background': color,
                'highlight': {
                    'border': bcolor,
                    'background': color,
                },
                'hover': {
                    'border': bcolor,
                    'background': color,
                },
            },
            'label': ' ',
            'labelHighlightBold': False,
            'physics': bool(physics),
            'shape': NODE_STYLES[style],
            'size': size // 2,
            'x': round((x - 0.5) * (0.9 * local_width - 24)) + dx,
            'y': round((0.5 - y) * (0.9 * local_height - 24)) + dy,
        }
        label = g.nodes[n].get('label', None)
        if label:
            options['title'] = label
        network.add_node(n, **options)

    for n, m in g.edges:
        if n == m:
            warn('self loops are not supported, ignoring')
        else:
            _, _, width, style, color, _, _, _ = _build_edge_key(g, n, m)
            color = _convert(color)
            options = {
                'color': {
                    'color': color,
                    'highlight': color,
                    'hover': color,
                },
                'dashes': EDGE_STYLES[style],
                'labelHighlightBold': False,
                'selectionWidth': 0,
                'width': width,
            }
            label = g.edges[n, m].get('label', None)
            if label:
                options['title'] = label
            network.add_edge(n, m, **options)
            if network.directed:
                network.edges[-1]['arrows'] = {
                    'to': {
                        'scaleFactor': EDGE_SCALE,
                    },
                }

    if path is None:
        if not os.path.exists(CACHE_DIR):
            os.mkdir(CACHE_DIR)
        path = os.path.join(CACHE_DIR, '{}.html'.format(id(g)))
    else:
        path = str(path)

    iframe = network.show(path)

    # parameters estimated from screenshots
    iframe.width += 10
    iframe.height += 10

    display(iframe)


def draw(g, toolbar=False):
    """Render a static visualization of a graph.

    The visualization is powered by `Plotly <https://plot.ly/python/>`_, based
    on the :ref:`visual attributes <visual-attributes>`, completely consistent
    with the :func:`Animation <freeman.drawing.Animation>` class, and mostly
    consistent with the :func:`interact <freeman.drawing.interact>` function.
    The only significative difference is that a pair of edges **(n, m)** and
    **(m, n)** in a directed graph is rendered as two separate edges in opposite
    directions. Such rendering is more faithful to the graph density.

    :type g: NetworkX Graph or DiGraph
    :param g: The graph to visualize.

    :type toolbar: bool
    :param toolbar: Whether to enable the toolbar. This is particularly useful for saving the
                    visualization to a PNG file.
    """
    local_width, local_height, local_bottom, local_left, local_right, local_top = _build_graph_key(g)
    local_width += local_left + local_right
    local_height += local_bottom + local_top

    node_traces = {}
    node_label_trace = _build_node_label_trace(local_width, local_height, local_bottom, local_left, local_right, local_top)
    for n in g.nodes:
        size, style, color, bwidth, bcolor, labpos = _build_node_key(g, n)
        key = (size, style, color, bwidth, bcolor, labpos)
        if key not in node_traces:
            node_traces[key] = _build_node_trace(size, style, color, bwidth, bcolor, labpos)
        _add_node(g, n, node_traces[key])

    edge_traces = {}
    edge_label_trace = _build_edge_label_trace()
    for n, m in g.edges:
        if n == m:
            warn('self loops are not supported, ignoring')
        else:
            n_size, m_size, width, style, color, labflip, labdist, labfrac = _build_edge_key(g, n, m)
            key = (width, style, color)
            if key not in edge_traces:
                edge_traces[key] = _build_edge_trace(width, style, color)
            _add_edge(g, n, m, edge_traces[key], edge_label_trace, local_width, local_height, n_size, m_size, labflip, labdist, labfrac)

    data = list(edge_traces.values())
    data.extend(node_traces.values())
    data.append(edge_label_trace)
    data.append(node_label_trace)

    layout = _build_layout(local_width, local_height)
    if isinstance(g, nx.DiGraph):
        layout['xaxis']['fixedrange'] = True
        layout['yaxis']['fixedrange'] = True

    figure = {
        'data': data,
        'layout': layout,
    }

    plotly.offline.iplot(figure, config={'displayModeBar': toolbar}, show_link=False)


class Animation:
    """An Animation renders a dynamic visualization of a sequence of graphs.

    The visualization is powered by `Plotly <https://plot.ly/python/>`_, based
    on the :ref:`visual attributes <visual-attributes>`, completely consistent
    with the :func:`draw <freeman.drawing.draw>` function, and mostly consistent
    with the :func:`interact <freeman.drawing.interact>` function. The only
    significative difference is that a pair of edges **(n, m)** and **(m, n)**
    in a directed graph is rendered as two separate edges in opposite
    directions. Such rendering is more faithful to the graph density.

    :type width: int
    :param width: Animation width, in pixels. Must be positive.

    :type height: int
    :param height: Animation height, in pixels. Must be positive.
    """
    def __init__(self, width=None, height=None):
        if width is not None:
            if not isinstance(width, int):
                raise TypeError('animation width must be an integer')
            if width <= 0:
                raise ValueError('animation width must be positive')

        if height is not None:
            if not isinstance(height, int):
                raise TypeError('animation height must be an integer')
            if height <= 0:
                raise ValueError('animation height must be positive')

        self.width = width
        self.height = height
        self.graphs = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.play()

    def _render(self, g, h, local_width, local_height):
        local_bottom, local_left, local_right, local_top = _build_graph_padding(g)
        local_width += local_left + local_right
        local_height += local_bottom + local_top

        node_traces = []
        node_label_trace = _build_node_label_trace(local_width, local_height, local_bottom, local_left, local_right, local_top)
        for n in h.nodes:
            if g.has_node(n):
                size, style, color, bwidth, bcolor, labpos = _build_node_key(g, n)
                node_trace = _build_node_trace(size, style, color, bwidth, bcolor, labpos)
                _add_node(g, n, node_trace)
            else:
                size, style, _, bwidth, _, labpos = _build_node_key(h, n)
                node_trace = _build_node_trace(size, style, (255, 255, 255, 0.0), bwidth, (255, 255, 255, 0.0), labpos)
                _add_node(h, n, node_trace)
            node_traces.append(node_trace)

        edge_traces = []
        edge_label_trace = _build_edge_label_trace()
        for n, m in h.edges:
            if n == m:
                warn('self loops are not supported, ignoring')
            else:
                if g.has_edge(n, m):
                    n_size, m_size, width, style, color, labflip, labdist, labfrac = _build_edge_key(g, n, m)
                    edge_trace = _build_edge_trace(width, style, color)
                    _add_edge(g, n, m, edge_trace, edge_label_trace, local_width, local_height, n_size, m_size, labflip, labdist, labfrac)
                else:
                    n_size, m_size, width, style, _, labflip, labdist, labfrac = _build_edge_key(h, n, m)
                    edge_trace = _build_edge_trace(width, style, (255, 255, 255, 0.0))
                    _add_edge(h, n, m, edge_trace, edge_label_trace, local_width, local_height, n_size, m_size, labflip, labdist, labfrac)
                edge_traces.append(edge_trace)

        data = edge_traces
        data.extend(node_traces)
        data.append(edge_label_trace)
        data.append(node_label_trace)

        frame = {
            'data': data,
        }

        return frame

    def rec(self, g):
        """Record a graph.

        The method simply stores a copy of the graph. The original graph is not
        stored because it is expected to change after being recorded.

        :type g: NetworkX Graph or DiGraph
        :param g: The graph to record.
        """
        self.graphs.append(g.copy())

    def play(self):
        """Play recorded graphs.

        If the animation constructor has been called with ``width=None``, checks
        if all recorded graphs have the same width. If they do, such width is
        used for displaying the animation. Otherwise, the default value for
        graph width is used. Same for ``height=None``.

        At least two graphs must have been recorded.
        """
        if len(self.graphs) < 2:
            raise ValueError('animation must have at least two recs')

        h = None
        width = self.width
        height = self.height
        last = self.graphs[-1]
        number_of_nodes = last.number_of_nodes()
        number_of_edges = last.number_of_edges()
        local_width = _build_graph_width(last)
        local_height = _build_graph_height(last)

        for g in self.graphs[:-1]:
            if h is None and (g.number_of_nodes() != number_of_nodes or g.number_of_edges() != number_of_edges):
                h = nx.compose_all(self.graphs)
            if width is None and _build_graph_width(g) != local_width:
                width = graph_width
            if height is None and _build_graph_height(g) != local_height:
                height = graph_height

        if width is None:
            width = local_width
        if height is None:
            height = local_height

        frames = []
        for i, g in enumerate(self.graphs):
            if h is None:
                frames.append(self._render(g, g, width, height))
            else:
                if g != last:
                    next = self.graphs[i + 1]
                    for n in next.nodes:
                        h.nodes[n].update(next.nodes[n])
                    for n, m in next.edges:
                        h.edges[n, m].update(next.edges[n, m])
                frames.append(self._render(g, h, width, height))

        # parameters estimated from screenshots
        width = 1.05 * width + 72
        height = 1.00 * height + 76

        steps = []
        for i, frame in enumerate(frames):
            frame['name'] = i
            step = {
                'args': [[i], {'frame': {'redraw': False}, 'mode': 'immediate'}],
                'label': '',
                'method': 'animate',
            }
            steps.append(step)

        layout = _build_layout(width, height)
        layout.update({
            'updatemenus': [
                {
                    'buttons': [
                        {
                            'args': [None, {'frame': {'redraw': False}, 'fromcurrent': True}],
                            'label': 'Play',
                            'method': 'animate',
                        },
                        {
                            'args': [[None], {'frame': {'redraw': False}, 'mode': 'immediate'}],
                            'label': 'Pause',
                            'method': 'animate',
                        },
                    ],
                    'showactive': True,
                    'type': 'buttons',
                },
            ],
            'sliders': [
                {
                    'currentvalue': {'visible': False},
                    'steps': steps,
                },
            ],
        })

        figure = {
            'data': frames[0]['data'],
            'layout': layout,
            'frames': frames,
        }

        plotly.offline.iplot(figure, config={'staticPlot': True}, show_link=False)


plotly.offline.init_notebook_mode(connected=True)
