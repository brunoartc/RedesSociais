from math import isclose, isinf, log
from statistics import mean
from colorsys import rgb_to_hsv, hsv_to_rgb


def _stringify(value, ndigits):
    if isinstance(value, float):
        if isinf(value):
            return '∞'

        value = round(value, ndigits)

    return str(value)


def _transform(h, s, v):
    sr, sg, sb = hsv_to_rgb(h, s, v)

    r = round(sr * 255)
    g = round(sg * 255)
    b = round(sb * 255)

    return r, g, b


def _assert_bounds(iterable, lower, upper):
    values = list(assert_numerics(iterable))

    if lower is None:
        lower = min(values)
    else:
        lower = assert_numeric(lower)
        if any(value < lower for value in values):
            raise ValueError('lower must be below all values')

    if upper is None:
        upper = max(values)
    else:
        upper = assert_numeric(upper)
        if any(value > upper for value in values):
            raise ValueError('upper must be above all values')

    return values, lower, upper


def _assert_reference(values, lower, upper, middle):
    if middle is None:
        middle = mean(values)
    else:
        middle = assert_numeric(middle)
        if middle < lower or middle > upper:
            raise ValueError('middle must be between lower and upper')

    return middle


def _assert_hue(color):
    if not isinstance(color, (tuple, list)):
        raise TypeError('color must be a tuple or list')
    if len(color) != 3:
        raise ValueError('color must have exactly three elements')
    if not isinstance(color[0], int) or not isinstance(color[1], int) or not isinstance(color[2], int):
        raise TypeError('all color elements must be integers')
    if color[0] < 0 or color[0] > 255 or color[1] < 0 or color[1] > 255 or color[2] < 0 or color[2] > 255:
        raise ValueError('all color elements must be between 0 and 255')

    sr = color[0] / 255
    sg = color[1] / 255
    sb = color[2] / 255

    h, _, _ = rgb_to_hsv(sr, sg, sb)

    return h


def assert_numeric(value):
    if not isinstance(value, (int, float)):
        raise TypeError('value must be numeric')
    return value


def assert_numerics(values):
    return (assert_numeric(value) for value in values)


def extract_node(g, n, map):
    if isinstance(map, Log):
        return log(extract_node(g, n, map.wrapped) + map.shift)
    if isinstance(map, str):
        return g.nodes[n][map]
    if isinstance(map, dict):
        return map[n]
    if callable(map):
        return map(n)
    raise TypeError('map must be a string, a dictionary, or a callable')


def extract_edge(g, n, m, map):
    if isinstance(map, Log):
        return log(extract_edge(g, n, m, map.wrapped) + map.shift)
    if isinstance(map, str):
        return g.edges[n, m][map]
    if isinstance(map, dict):
        return map[n, m]
    if callable(map):
        return map(n, m)
    raise TypeError('map must be a string, a dictionary, or a callable')


def extract_nodes(g, map):
    return (extract_node(g, n, map) for n in g.nodes)


def extract_edges(g, map):
    return (extract_edge(g, n, m, map) for n, m in g.edges)


def label_nodes(g, map=None, ndigits=2):
    if map is None:
        labels = (str(n) for n in g.nodes)
    else:
        labels = [_stringify(extract_node(g, n, map), ndigits) for n in g.nodes]

    for n, label in zip(g.nodes, labels):
        g.nodes[n]['label'] = label


def label_edges(g, map=None, ndigits=2):
    if map is None:
        labels = (str((n, m)) for n, m in g.edges)
    else:
        labels = [_stringify(extract_edge(g, n, m, map), ndigits) for n, m in g.edges]

    for (n, m), label in zip(g.edges, labels):
        g.edges[n, m]['label'] = label


def colorize_nodes(g, map=None):
    if map is None:
        groups = list(zip(g.nodes))
    else:
        groups = {}
        for n in g.nodes:
            value = extract_node(g, n, map)
            if value not in groups:
                groups[value] = []
            groups[value].append(n)
        groups = groups.values()

    h = 0
    s = 1 / len(groups)
    for group in groups:
        color = _transform(h, 1, 1)
        for n in group:
            g.nodes[n]['color'] = color
        h += s


def colorize_edges(g, map=None):
    if map is None:
        groups = list(zip(g.edges))
    else:
        groups = {}
        for n, m in g.edges:
            value = extract_edge(g, n, m, map)
            if value not in groups:
                groups[value] = []
            groups[value].append((n, m))
        groups = groups.values()

    h = 0
    s = 1 / len(groups)
    for group in groups:
        color = _transform(h, 1, 1)
        for n, m in group:
            g.edges[n, m]['color'] = color
        h += s


def scale_nodes_size(g, map, lower=None, upper=None):
    values, lower, upper = _assert_bounds(extract_nodes(g, map), lower, upper)

    for n, value in zip(g.nodes, values):
        if isclose(lower, upper):
            sc = 0.5
        else:
            sc = (value - lower) / (upper - lower)

        g.nodes[n]['size'] = 5 + round(sc * 45)


def scale_edges_width(g, map, lower=None, upper=None):
    values, lower, upper = _assert_bounds(extract_edges(g, map), lower, upper)

    for (n, m), value in zip(g.edges, values):
        if isclose(lower, upper):
            sc = 0.5
        else:
            sc = (value - lower) / (upper - lower)

        g.edges[n, m]['width'] = 1 + round(sc * 9)


def scale_nodes_dark(g, map, lower=None, upper=None, color=None):
    values, lower, upper = _assert_bounds(extract_nodes(g, map), lower, upper)

    for n, value in zip(g.nodes, values):
        if isclose(lower, upper):
            sc = 0.5
        else:
            sc = (value - lower) / (upper - lower)

        if color is None:
            c = 255 - round(sc * 255)
            g.nodes[n]['color'] = (c, c, c)
        else:
            h = _assert_hue(color)
            g.nodes[n]['color'] = _transform(h, sc, 1)


def scale_edges_alpha(g, map, lower=None, upper=None, color=None):
    values, lower, upper = _assert_bounds(extract_edges(g, map), lower, upper)

    for (n, m), value in zip(g.edges, values):
        if isclose(lower, upper):
            sc = 0.5
        else:
            sc = (value - lower) / (upper - lower)

        if color is None:
            g.edges[n, m]['color'] = (0, 0, 0, sc)
        else:
            h = _assert_hue(color)
            g.edges[n, m]['color'] = (*_transform(h, 1, 1), sc)


def heat_nodes(g, map, lower=None, upper=None, middle=None):
    values, lower, upper = _assert_bounds(extract_nodes(g, map), lower, upper)

    middle = _assert_reference(values, lower, upper, middle)

    for n, value in zip(g.nodes, values):
        if isclose(lower, upper):
            g.nodes[n]['color'] = (255, 255, 255)
        else:
            if value < middle:
                sc = (value - lower) / (middle - lower)
                c = round(sc * 255)
                g.nodes[n]['color'] = (c, c, 255)
            else:
                sc = (value - middle) / (upper - middle)
                c = 255 - round(sc * 255)
                g.nodes[n]['color'] = (255, c, c)


def heat_edges(g, map, lower=None, upper=None, middle=None):
    values, lower, upper = _assert_bounds(extract_edges(g, map), lower, upper)

    middle = _assert_reference(values, lower, upper, middle)

    for (n, m), value in zip(g.edges, values):
        if isclose(lower, upper):
            g.edges[n, m]['color'] = (255, 255, 255, 0.0)
        else:
            if value < middle:
                sc = (value - lower) / (middle - lower)
                g.edges[n, m]['color'] = (0, 0, 255, 1 - sc)
            else:
                sc = (value - middle) / (upper - middle)
                g.edges[n, m]['color'] = (255, 0, 0, sc)


class Log:
    def __init__(self, wrapped, shift=0):
        self.wrapped = wrapped

        self.shift = shift
