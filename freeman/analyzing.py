import pandas as pd
import networkx as nx

try:
    import seaborn as sns
except NotImplementedError:
    sns = None

from math import isclose, sqrt, log
from statistics import variance
from random import choices, sample
from itertools import product, permutations, combinations
from scipy.stats import shapiro, normaltest, kstest, norm, powerlaw, expon, pearsonr, chi2_contingency, ttest_1samp, ttest_ind, ttest_rel
from scipy.cluster.hierarchy import dendrogram
from statsmodels.api import OLS, Logit

try:
    from prince import CA

    from matplotlib import pyplot as plt
except NotImplementedError:
    pass

from .exploring import extract_nodes, extract_edges, Log
from .moving import normalize


DPI = 100

DEC = 6


def _varzero(a):
    return isclose(variance(a), 0)


def _product(population, k, max_perm):
    return (choices(population, k=k) for _ in range(max_perm))


def _permutations(population, max_perm):
    return (sample(population, len(population)) for _ in range(max_perm))


def _series(iterable):
    if iterable is None:
        return None
    if isinstance(iterable, pd.Series):
        return iterable
    if isinstance(iterable, Log):
        return _series(iterable.wrapped).apply(lambda v: log(v) + iterable.shift)
    return pd.Series(iterable)


def _iterable(df, col):
    if col is None:
        return None
    if isinstance(col, Log):
        return Log(_iterable(df, col.wrapped), col.shift)
    return df[col]


def _cortest(x, y, max_perm):
    x = _series(x)
    y = _series(y)
    r, p = pearsonr(x, y)
    if max_perm is not None:
        population = list(y)
        if max_perm == 0:
            resamples = permutations(population)
        else:
            resamples = _permutations(population, max_perm)
        above = 0
        total = 0
        for resample in resamples:
            result, _ = _cortest(x, resample, None)
            if (r < 0 and result <= r) or r == 0 or (r > 0 and result >= r):
                above += 1
            total += 1
        p = 2 * (above / total)
    return r, p


def _chitest(x, y, max_perm):
    x = _series(x)
    y = _series(y)
    observed = pd.crosstab(x, y)
    chi2, p, _, _ = chi2_contingency(observed)
    n = len(x)
    r, k = observed.shape
    phi2 = max(0, chi2 / n - ((k - 1) * (r - 1)) / (n - 1))
    k -= (k - 1)**2 / (n - 1)
    r -= (r - 1)**2 / (n - 1)
    v = sqrt(phi2 / min(k - 1, r - 1))
    if max_perm is not None:
        population = list(y)
        if max_perm == 0:
            resamples = permutations(population)
        else:
            resamples = _permutations(population, max_perm)
        above = 0
        total = 0
        for resample in resamples:
            result, _ = _chitest(x, resample, None)
            if result >= v:
                above += 1
            total += 1
        p = above / total
    return v, p


def _indtest(a, b, max_perm):
    a = _series(a)
    b = _series(b)
    length = len(a)
    if length == 0 or len(b) == 0 or (_varzero(a) and _varzero(b)):
        return None
    t, p = ttest_ind(a, b, equal_var=False)
    if max_perm is not None:
        population = list(a) + list(b)
        if max_perm == 0:
            resamples = permutations(population)
        else:
            resamples = _permutations(population, max_perm)
        above = 0
        total = 0
        for resample in resamples:
            result = _indtest(resample[:length], resample[length:], None)
            if result is None:
                return None
            result = result[0]
            if (t < 0 and result <= t) or t == 0 or (t > 0 and result >= t):
                above += 1
            total += 1
        p = 2 * (above / total)
    return t, p


def _reltest(a, b, max_perm):
    a = _series(a)
    b = _series(b)
    length = len(a)
    if length == 0 or length != len(b) or _varzero(A - B for A, B in zip(a, b)):
        return None
    t, p = ttest_rel(a, b)
    if max_perm is not None:
        population = (False, True)
        if max_perm == 0:
            resamples = product(population, repeat=length)
        else:
            resamples = _product(population, length, max_perm)
        above = 0
        total = 0
        for resample in resamples:
            resample_a = []
            resample_b = []
            for i, keep in enumerate(resample):
                if keep:
                    resample_a.append(a[i])
                    resample_b.append(b[i])
                else:
                    resample_a.append(b[i])
                    resample_b.append(a[i])
            result = _reltest(resample_a, resample_b, None)
            if result is None:
                return None
            result = result[0]
            if (t < 0 and result <= t) or t == 0 or (t > 0 and result >= t):
                above += 1
            total += 1
        p = 2 * (above / total)
    return t, p


def set_nodeframe(g):
    data = {
        'id': g.nodes,
    }
    g.nodeframe = pd.DataFrame(data)


def set_edgeframe(g):
    data = {
        'source': [n for n, m in g.edges],
        'target': [m for n, m in g.edges],
    }
    g.edgeframe = pd.DataFrame(data)


def set_nodecol(g, col, map):
    g.nodeframe[col] = list(extract_nodes(g, map))


def set_edgecol(g, col, map):
    g.edgeframe[col] = list(extract_edges(g, map))


def concat(dfs, col):
    for key, df in dfs.items():
        df[col] = key
    return pd.concat(dfs.values())


def concat_nodes(graphs, col):
    return concat({key: g.nodeframe for key, g in graphs.items()}, col)


def concat_edges(graphs, col):
    return concat({key: g.edgeframe for key, g in graphs.items()}, col)


def distest_loose(x):
    x = _series(x)
    data = {
        'Shapiro-Wilk (normal)': shapiro(x),
        'D\'Agostino-Pearson (normal)': normaltest(x),
        'Kolmogorov-Smirnov (normal)': kstest(x, 'norm', norm.fit(x)),
        'Kolmogorov-Smirnov (powerlaw)': kstest(x, 'powerlaw', powerlaw.fit(x)),
        'Kolmogorov-Smirnov (exponential)': kstest(x, 'expon', expon.fit(x)),
    }
    keys = data.keys()
    values = (p for _, p in data.values())
    return pd.DataFrame(values, keys, ['p-value']).round(DEC)


def distest(df, x):
    return distest_loose(_iterable(df, x))


def distest_nodes(g, x):
    return distest(g.nodeframe, x)


def distest_edges(g, x):
    return distest(g.edgeframe, x)


def cortest_loose(x, y, max_perm=None):
    r, p = _cortest(x, y, max_perm)
    return round(r, DEC), round(p, DEC)


def cortest(df, x, y, max_perm=None):
    return cortest_loose(_iterable(df, x), _iterable(df, y), max_perm)


def cortest_nodes(g, x, y, max_perm=None):
    return cortest(g.nodeframe, x, y, max_perm)


def cortest_edges(g, x, y, max_perm=None):
    return cortest(g.edgeframe, x, y, max_perm)


def chitest_loose(x, y, max_perm=None):
    v, p = _chitest(x, y, max_perm)
    return round(v, DEC), round(p, DEC)


def chitest(df, x, y, max_perm=None):
    return chitest_loose(_iterable(df, x), _iterable(df, y), max_perm)


def chitest_nodes(g, x, y, max_perm=None):
    return chitest(g.nodeframe, x, y, max_perm)


def chitest_edges(g, x, y, max_perm=None):
    return chitest(g.edgeframe, x, y, max_perm)


def onetest_loose(a, mean):
    a = _series(a)
    if len(a) == 0 or _varzero(a):
        return None
    _, p = ttest_1samp(a, mean)
    return round(p, DEC)


def onetest(df, a, mean):
    return onetest_loose(_iterable(df, a), mean)


def indtest_loose(a, b, max_perm=None):
    result = _indtest(a, b, max_perm)
    if result is None:
        return None
    return round(result[1], DEC)


def indtest(df, a, b, max_perm=None):
    return indtest_loose(_iterable(df, a), _iterable(df, b), max_perm)


def reltest_loose(a, b, max_perm=None):
    result = _reltest(a, b, max_perm)
    if result is None:
        return None
    return round(result[1], DEC)


def reltest(df, a, b, max_perm=None):
    return reltest_loose(_iterable(df, a), _iterable(df, b), max_perm)


def reltest_nodes(g, a, b, max_perm=None):
    return reltest(g.nodeframe, a, b, max_perm)


def reltest_edges(g, a, b, max_perm=None):
    return reltest(g.edgeframe, a, b, max_perm)


def mixtest_loose(x, y, max_perm=None):
    data = {}
    for X, Y in zip(_series(x), _series(y)):
        if Y not in data:
            data[Y] = []
        data[Y].append(X)
    result = []
    index = []
    for y1, y2 in combinations(data, 2):
        result.append(indtest_loose(data[y1], data[y2], max_perm))
        index.append('{}, {}'.format(y1, y2))
    return pd.DataFrame(result, index, ['p-value'])


def mixtest(df, x, y, max_perm=None):
    return mixtest_loose(_iterable(df, x), _iterable(df, y), max_perm)


def mixtest_nodes(g, x, y, max_perm=None):
    return mixtest(g.nodeframe, x, y, max_perm)


def mixtest_edges(g, x, y, max_perm=None):
    return mixtest(g.edgeframe, x, y, max_perm)


def linregress_loose(X, y, *args, **kwargs):
    X = list(zip(*(_series(x) for x in X)))
    y = _series(y)
    model = OLS(y, X)
    result = model.fit(*args, **kwargs)
    return result.summary()


def linregress(df, X, y, *args, **kwargs):
    return linregress_loose((_iterable(df, x) for x in X), _iterable(df, y), *args, **kwargs)


def linregress_nodes(g, X, y, *args, **kwargs):
    return linregress(g.nodeframe, X, y, *args, **kwargs)


def linregress_edges(g, X, y, *args, **kwargs):
    return linregress(g.edgeframe, X, y, *args, **kwargs)


def logregress_loose(X, y, *args, **kwargs):
    X = list(zip(*(_series(x) for x in X)))
    y = _series(y)
    model = Logit(y, X)
    result = model.fit(*args, **kwargs)
    return result.summary()


def logregress(df, X, y, *args, **kwargs):
    return logregress_loose((_iterable(df, x) for x in X), _iterable(df, y), *args, **kwargs)


def logregress_nodes(g, X, y, *args, **kwargs):
    return logregress(g.nodeframe, X, y, *args, **kwargs)


def logregress_edges(g, X, y, *args, **kwargs):
    return logregress(g.edgeframe, X, y, *args, **kwargs)


def intencode(df, col, order=None):
    values = df[col].unique()
    if order is None:
        order = tuple(sorted(values))
    else:
        if not isinstance(order, (tuple, list)):
            raise TypeError('order must be a tuple or list')
        if len(order) > len(set(order)):
            raise ValueError('order has repeated values')
        if any(value not in order for value in values):
            raise ValueError('column has values not in order')
    new = col + '_order'
    df[new] = df[col].apply(lambda v: order.index(v))
    return new


def intencode_nodes(g, col, order=None):
    return intencode(g.nodeframe, col, order)


def intencode_edges(g, col, order=None):
    return intencode(g.edgeframe, col, order)


def binencode(df, col):
    values = df[col].unique()
    news = tuple('{}_{}'.format(col, value) for value in values)
    for new, value in zip(news, values):
        df[new] = df[col].apply(lambda v: int(v == value))
    return news


def binencode_nodes(g, col):
    return binencode(g.nodeframe, col)


def binencode_edges(g, col):
    return binencode(g.edgeframe, col)


def resize_next_plot(width, height):
    plt.figure(figsize=(width / DPI, height / DPI), dpi=DPI)


def resize_all_plots(width, height):
    plt.rcParams['figure.figsize'] = (width / DPI, height / DPI)
    plt.rcParams['figure.dpi'] = DPI


def displot_loose(x):
    sns.distplot(_series(x))


def displot(df, x):
    displot_loose(_iterable(df, x))


def displot_nodes(g, x):
    displot(g.nodeframe, x)


def displot_edges(g, x):
    displot(g.edgeframe, x)


def barplot_loose(x, control=None):
    sns.countplot(_series(x), hue=_series(control))


def barplot(df, x, control=None):
    barplot_loose(_iterable(df, x), _iterable(df, control))


def barplot_nodes(g, x, control=None):
    barplot(g.nodeframe, x, control)


def barplot_edges(g, x, control=None):
    barplot(g.edgeframe, x, control)


def linplot_loose(x, y, control=None):
    sns.lineplot(_series(x), _series(y), _series(control))


def linplot(df, x, y, control=None):
    linplot_loose(_iterable(df, x), _iterable(df, y), _iterable(df, control))


def linplot_nodes(g, x, y, control=None):
    linplot(g.nodeframe, x, y, control)


def linplot_edges(g, x, y, control=None):
    linplot(g.edgeframe, x, y, control)


def scaplot_loose(x, y, control=None):
    sns.scatterplot(_series(x), _series(y), _series(control))


def scaplot(df, x, y, control=None):
    scaplot_loose(_iterable(df, x), _iterable(df, y), _iterable(df, control))


def scaplot_nodes(g, x, y, control=None):
    scaplot(g.nodeframe, x, y, control)


def scaplot_edges(g, x, y, control=None):
    scaplot(g.edgeframe, x, y, control)


def matplot_loose(X, control=None):
    X = [_series(x) for x in (*X, control)]
    for i, x in enumerate(X):
        if x is not None:
            if x.name is None:
                x.name = i
    df = pd.concat(X, 1)
    X = [None if x is None else x.name for x in X]
    sns.pairplot(df, X[-1], vars=X[:-1])


def matplot(df, X, control=None):
    matplot_loose((_iterable(df, x) for x in X), _iterable(df, control))


def matplot_nodes(g, X, control=None):
    matplot(g.nodeframe, X, control)


def matplot_edges(g, X, control=None):
    matplot(g.edgeframe, X, control)


def valcount_loose(x, order=None, transpose=False):
    x = _series(x)
    df = pd.DataFrame(x.value_counts(True)).round(2)
    df.columns = ['All']
    if order is not None:
        df = df.reindex(order)
    if transpose:
        return df.transpose()
    return df


def valcount(df, x, order=None, transpose=False):
    return valcount_loose(_iterable(df, x), order, transpose)


def valcount_nodes(g, x, order=None, transpose=False):
    return valcount(g.nodeframe, x, order, transpose)


def valcount_edges(g, x, order=None, transpose=False):
    return valcount(g.edgeframe, x, order, transpose)


def contable_loose(x, y):
    return pd.crosstab(_series(x), _series(y), margins=True, normalize=True)


def contable(df, x, y):
    return contable_loose(_iterable(df, x), _iterable(df, y))


def contable_nodes(g, x, y):
    return contable(g.nodeframe, x, y)


def contable_edges(g, x, y):
    return contable(g.edgeframe, x, y)


def corplot_loose(x, y):
    observed = pd.crosstab(_series(x), _series(y))
    ca = CA()
    ca.fit(observed)
    ca.plot_coordinates(observed)


def corplot(df, x, y):
    corplot_loose(_iterable(df, x), _iterable(df, y))


def corplot_nodes(g, x, y):
    corplot(g.nodeframe, x, y)


def corplot_edges(g, x, y):
    corplot(g.edgeframe, x, y)


def boxplot_loose(x, y, control=None):
    sns.boxplot(_series(x), _series(y), _series(control), orient='h')


def boxplot(df, x, y, control=None):
    boxplot_loose(_iterable(df, x), _iterable(df, y), _iterable(df, control))


def boxplot_nodes(g, x, y, control=None):
    boxplot(g.nodeframe, x, y, control)


def boxplot_edges(g, x, y, control=None):
    boxplot(g.edgeframe, x, y, control)


def girvan_newman(g):
    d = 0.0
    linkage = []
    clusters = []

    for C in reversed(list(nx.community.girvan_newman(g))):
        for c in C:
            if c not in clusters:
                if len(c) > 1:
                    i = 0
                    while clusters[i] is None or not clusters[i].issubset(c):
                        i += 1
                    j = clusters.index(c - clusters[i])
                    d += 1
                    linkage.append([i, j, d, len(c)])
                    clusters[i] = None
                    clusters[j] = None
                clusters.append(c)

    while len(linkage) < g.number_of_nodes() - 1:
        j = len(clusters) - 1
        i = 0
        while clusters[i] is None:
            i += 1
        c = clusters[i] | clusters[j]
        d += 1
        linkage.append([i, j, d, len(c)])
        clusters[i] = None
        clusters[j] = None
        clusters.append(c)

    labels = [g.nodes[n].get('label', str(n)) for n in g.nodes]

    dendrogram(linkage, orientation='right', labels=labels)


def corplot_graph(g, nodes, weight='weight', plot=True):
    other = [m for m in g.nodes if m not in nodes]

    for n, m in g.edges:
        if (n in nodes and m in nodes) or (n in other and m in other):
            raise ValueError('nodes do not define a bipartition')
        if isinstance(g, nx.DiGraph) and (n in other and m in nodes):
            raise ValueError('nodes do not define a directed bipartition')

    nodes = [n for n in nodes if g.degree(n) > 0]
    other = [m for m in other if g.degree(m) > 0]

    sparse = nx.bipartite.biadjacency_matrix(g, nodes, other, weight=weight)
    matrix = sparse.toarray()

    observed = pd.DataFrame(matrix, nodes, other)
    ca = CA()
    ca.fit(observed)

    if plot:
        ca.plot_coordinates(observed)

    h = g.subgraph(nodes + other).copy()

    pos = ca.row_coordinates(observed)
    for n, x, y in zip(nodes, pos[0], pos[1]):
        h.nodes[n]['pos'] = (x, y)
        h.nodes[n]['color'] = (76, 116, 172)

    pos = ca.column_coordinates(observed)
    for m, x, y in zip(other, pos[0], pos[1]):
        h.nodes[m]['pos'] = (x, y)
        h.nodes[m]['color'] = (219, 130, 87)

    normalize(h)

    return h


if sns is not None:
    sns.set()
