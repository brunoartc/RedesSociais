"""Module responsible for positioning graph nodes.
"""
import networkx as nx

from math import isclose

from .exploring import assert_numerics, extract_nodes


def step_layout(g, ego=None, iterations=1, weight='weight'):
    before = nx.get_node_attributes(g, 'pos')

    fixed = None if ego is None else [ego]

    return nx.spring_layout(g, pos=before, fixed=fixed, iterations=iterations, weight=weight)


LAYOUTS = {
    'bipartite': nx.bipartite_layout,
    'circular': nx.circular_layout,
    'kamada_kawai': nx.kamada_kawai_layout,
    'planar': nx.planar_layout,
    'random': nx.random_layout,
    'shell': nx.shell_layout,
    'spring': nx.spring_layout,
    'spectral': nx.spectral_layout,
    'step': step_layout,
}


def normalize(g):
    if g.number_of_nodes() == 0:
        return

    X = []
    Y = []
    for n in g.nodes:
        x, y = g.nodes[n]['pos']
        X.append(x)
        Y.append(y)

    xmin = min(X)
    xmax = max(X) - xmin
    ymin = min(Y)
    ymax = max(Y) - ymin

    for n in g.nodes:
        x, y = g.nodes[n]['pos']
        x = 0.5 if isclose(xmax, 0) else (x - xmin) / xmax
        y = 0.5 if isclose(ymax, 0) else (y - ymin) / ymax
        g.nodes[n]['pos'] = (x, y)


def scatter(g, xmap, ymap):
    X = list(assert_numerics(extract_nodes(g, xmap)))
    Y = list(assert_numerics(extract_nodes(g, ymap)))

    for n, x, y in zip(g.nodes, X, Y):
        g.nodes[n]['pos'] = (x, y)

    normalize(g)


def move(g, key, *args, **kwargs):
    if key not in LAYOUTS:
        raise KeyError('layout key must be one of the following: ' + ', '.join('"{}"'.format(k) for k in LAYOUTS))

    layout = LAYOUTS[key]

    after = layout(g, *args, **kwargs)

    for n, (x, y) in after.items():
        x = float(x)
        y = float(y)
        g.nodes[n]['pos'] = (x, y)

    normalize(g)


def move_copy(g, h, key, *args, **kwargs):
    move(h, key, *args, **kwargs)

    for n in g.nodes:
        g.nodes[n]['pos'] = h.nodes[n]['pos']


def move_inverse(g, key, weight, *args, **kwargs):
    h = g.copy()
    for n, m in h.edges:
        if weight in g.edges[n, m]:
            h.edges[n, m][weight] = 1 / g.edges[n, m][weight]

    move_copy(g, h, key, *args, weight=weight, **kwargs)


def move_complement(g, key, *args, **kwargs):
    h = nx.complement(g)
    for n in h.nodes:
        h.nodes[n].update(g.nodes[n])

    move_copy(g, h, key, *args, **kwargs)
