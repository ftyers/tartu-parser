import sys
from collections import defaultdict
import argparse
import operator

# --------------------------------------------------------------------------------- #
# Main part of the code taken from:
# https://github.com/mlbright/edmonds/blob/master/edmonds/edmonds.py

def _load(arcs, weights):
    g = {}
    for (src, dst) in arcs:
        if src in g:
            g[src][dst] = weights[(src, dst)]
        else:
            g[src] = {dst: weights[(src, dst)]}
    return g


def _reverse(graph):
    r = {}
    for src in graph:
        for (dst, c) in graph[src].items():
            if dst in r:
                r[dst][src] = c
            else:
                r[dst] = {src: c}
    return r


def _getCycle(n, g, visited=set(), cycle=[]):
    visited.add(n)
    cycle += [n]
    if n not in g:
        return cycle
    for e in g[n]:
        if e not in visited:
            cycle = _getCycle(e, g, visited, cycle)
    return cycle


def _mergeCycles(cycle, G, RG, g, rg):
    allInEdges = []
    minInternal = None
    minInternalWeight = 100000000
    print(RG)
    # find minimal internal edge weight
    for n in cycle:
        print(n)
        for e in RG[n]:
            if e in cycle:
                if minInternal is None or RG[n][e] < minInternalWeight:
                    minInternal = (n, e)
                    minInternalWeight = RG[n][e]
                    continue
            else:
                allInEdges.append((n, e))

                # find the incoming edge with minimum modified cost
    minExternal = None
    minModifiedWeight = 0
    for s, t in allInEdges:
        u, v = rg[s].popitem()
        rg[s][u] = v
        w = RG[s][t] - (v - minInternalWeight)
        if minExternal is None or minModifiedWeight > w:
            minExternal = (s, t)
            minModifiedWeight = w

    u, w = rg[minExternal[0]].popitem()
    rem = (minExternal[0], u)
    rg[minExternal[0]].clear()
    if minExternal[1] in rg:
        rg[minExternal[1]][minExternal[0]] = w
    else:
        rg[minExternal[1]] = {minExternal[0]: w}
    if rem[1] in g:
        if rem[0] in g[rem[1]]:
            del g[rem[1]][rem[0]]
    if minExternal[1] in g:
        g[minExternal[1]][minExternal[0]] = w
    else:
        g[minExternal[1]] = {minExternal[0]: w}


# --------------------------------------------------------------------------------- #

def mst(root, G):
    """ The Chu-Lui/Edmond's algorithm
    arguments:
    root - the root of the MST
    G - the graph in which the MST lies
    returns: a graph representation of the MST
    Graph representation is the same as the one found at:
    http://code.activestate.com/recipes/119466/
    Explanation is copied verbatim here:
    The input graph G is assumed to have the following
    representation: A vertex can be any object that can
    be used as an index into a dictionary.  G is a
    dictionary, indexed by vertices.  For any vertex v,
    G[v] is itself a dictionary, indexed by the neighbors
    of v.  For any edge v->w, G[v][w] is the length of
    the edge.  This is related to the representation in
    <http://www.python.org/doc/essays/graphs.html>
    where Guido van Rossum suggests representing graphs
    as dictionaries mapping vertices to lists of neighbors,
    however dictionaries of edges have many advantages
    over lists: they can store extra information (here,
    the lengths), they support fast existence tests,
    and they allow easy modification of the graph by edge
    insertion and removal.  Such modifications are not
    needed here but are important in other graph algorithms.
    Since dictionaries obey iterator protocol, a graph
    represented as described here could be handed without
    modification to an algorithm using Guido's representation.
    Of course, G and G[v] need not be Python dict objects;
    they can be any other object that obeys dict protocol,
    for instance a wrapper in which vertices are URLs
    and a call to G[v] loads the web page and finds its links.
    """

    RG = _reverse(G)
    if root in RG:
        RG[root] = {}
    g = {}
    for n in RG:
        if len(RG[n]) == 0:
            continue
        minimum = 10000000
        s, d = None, None
        for e in RG[n]:
            if RG[n][e] < minimum:
                minimum = RG[n][e]
                s, d = n, e
        if d in g:
            g[d][s] = RG[s][d]
        else:
            g[d] = {s: RG[s][d]}

    cycles = []
    visited = set()
    for n in g:
        if n not in visited:
            cycle = _getCycle(n, g, visited)
            cycles.append(cycle)

    rg = _reverse(g)
    for cycle in cycles:
        if root in cycle:
            continue
        _mergeCycles(cycle, G, RG, g, rg)

    return g

def read_files(filenames):
    # TODO: HANDLE THE COMMENTS CORRECTLY, FROM EITHER INPUT FILE OR JUST UDPIPE COMMENTS
    files = defaultdict()
    nodes = defaultdict()
    names = defaultdict()
    range_tags = defaultdict(set)
    comments = defaultdict(list)
    for filename in filenames:
        print('Processing', filename)
        files[filename] = defaultdict()
        sent_id = 0

        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                words_in = line.strip().replace(' ', '\t').split('\t')
                if "-" in words_in[0]:
                    if "1" in words_in[0]:
                        range_tags[sent_id+1].add(tuple(words_in))
                    else:
                        range_tags[sent_id].add(tuple(words_in))
                elif words_in[0] == "1":
                    sent_id += 1
                    files[filename][sent_id] = []
                    current = sent_id
                    files[filename][current].append((words_in[0], words_in[1],
                                                     words_in[6], words_in[7]))
                    nodes[current] = nodes.get(current, defaultdict(set))
                    names[current] = names.get(current, defaultdict())
                    nodes[current][(words_in[6], words_in[0], words_in[7])].add(tuple(words_in))
                    names[current][(words_in[6], words_in[0])] = words_in[7]
                elif '#' in words_in[0]:
                    if "udpipe" in filename:
                        comments[sent_id+1].append(words_in)
                    else:
                        pass
                elif len(words_in) >= 8:
                    try:
                        files[filename][current].append((words_in[0], words_in[1],
                                                         words_in[6], words_in[7]))
                        nodes[current][(words_in[6],words_in[0],words_in[7])].add(tuple(words_in))
                        names[current][(words_in[6], words_in[0])] = words_in[7]
                    except IndexError:
                        pass
    return files,nodes,names,range_tags,comments


def weighting(single_file_graphs, weights):
    weighted_graph = defaultdict()
    for i in single_file_graphs:
        for j in single_file_graphs[i]:
            weighted_graph[j] = weighted_graph.get(j, defaultdict(int))
            for l in single_file_graphs[i][j]:
                weighted_graph[j][l] += weights[i]
    return weighted_graph

# --------------------------------------------------------------------------------- #

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--parses', '-p', type=str, nargs='+', required=True,
                        help="Filenames for parsed file(s)")
    parser.add_argument('--weights', '-w', type=str, nargs='+', required=True,
                        help="Weights for the parse files, enter in the same order as parse files.")
    parser.add_argument('--output', '-o', type=argparse.FileType('w', encoding='utf-8'),
                        default=sys.stdout, metavar='PATH',
                        help="Output file (default: standard output)")
    args = parser.parse_args()
    print(args)
    ## TODO: DEFINE WEIGHTS HERE
    weights = defaultdict(float)
    #k = 0.5
    #default_weights = defaultdict(float)
    #default_weights["malt"] = 72.54
    #default_weights["udpipe"] = 80.57
    #default_weights["bist"] = 62.97
    #default_weights["mst"] = 65.88
    for i in range(len(args.parses)):
        weights[args.parses[i]] += float(args.weights[i])
        #weights[i] += 0.5
    ## TODO: END OF DEFINE WEIGHTS

    file_data = read_files(args.parses)
    weighted = weighting(file_data[0],weights)
    nodes = file_data[1]
    arcs = defaultdict()
    names = file_data[2]
    range_tags = file_data[3]
    comments = file_data[4]
    for i in weighted:
        arcs[i] = defaultdict(float)
        for j in weighted[i]:
            if arcs[i][(j[2], j[0])] == 0.0:
                arcs[i][(j[2], j[0])] += 1 / weighted[i][j]
            else:
                arcs[i][(j[2], j[0])] *= 1 / weighted[i][j]
    finalnodes = defaultdict(list)
    for i in arcs:
        g = _load(arcs[i], arcs[i])
        h = mst('0', g)
        for s in h:
            for t in h[s]:
                x = names[i][(s, t)]
                a = list(list(nodes[i][(s, t, x)])[0])
                a[0] = int(a[0])
                finalnodes[i].append(a)
    try:
        #op = open(args.output, 'w', encoding='utf-8')
        #print("Got here")
        for i in finalnodes:
            for k in comments[i]:
                args.output.write('\t'.join(k) + '\n')
            if len(range_tags[i]) > 0:
                for j in sorted(finalnodes[i]):
                    for l in range_tags[i]:
                        l = list(filter(lambda a: a != '', l))
                        if str(j[0]) == str(l[0][0]):
                            args.output.write('\t'.join(l) + '\n')
                    args.output.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (
                        j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9]) + '\n')  # '''
            else:
                for j in sorted(finalnodes[i]):
                    args.output.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (
                        j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9]) + '\n')  # '''
            args.output.write('\n')
    except TypeError:
        for i in finalnodes:
            for k in comments[i]:
                print('\t'.join(k))
            if len(range_tags[i]) > 0:
                for j in sorted(finalnodes[i]):
                    for l in range_tags[i]:
                        l = list(filter(lambda a: a != '', l))
                        if str(j[0]) == str(l[0][0]):
                            print('\t'.join(l))
                    print('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (
                        j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9]))  # '''
            else:
                for j in sorted(finalnodes[i]):
                    print('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (
                        j[0], j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8], j[9]))  # '''
            print('\n')