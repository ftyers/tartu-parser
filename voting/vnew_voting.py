import sys
from collections import defaultdict
import argparse


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
                words_in = line.strip().split('\t')#replace(' ', '\t').split('\t')
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
                    nodes[current][words_in[0]].add(tuple(words_in))
                elif '#' in words_in[0]:
                    if "udpipe" in filename:
                        comments[sent_id+1].append(words_in)
                    else:
                        pass
                elif len(words_in) >= 8:
                    try:
                        files[filename][current].append((words_in[0], words_in[1],
                                                         words_in[6], words_in[7]))
                        nodes[current][words_in[0]].add(tuple(words_in))
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

def findMinimums(arcs):
    minArcs = defaultdict(tuple)
    for j in arcs:
        if j[0] != '0' or j[0] == '0':
            try:
                if minArcs[j[1]][1] > arcs[j]:
                    minArcs[j[1]] = (j[0], arcs[j])
            except IndexError:
                minArcs[j[1]] = (j[0], arcs[j])
    return minArcs

def dfs(graph, start, end):
    fringe = [(start, [])]
    while fringe:
        state, path = fringe.pop()
        if path and state == end:
            yield path
            continue
        for next_state in graph[state]:
            if next_state in path:
                continue
            fringe.append((next_state, path+[next_state]))

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
        #print("ARCS!!!!!!!!!!!!!!!!!!!!")
        #print(arcs[i])
        temp_nodes = set()
        for n in arcs[i]:
            temp_nodes.add(n[0])
            temp_nodes.add(n[1])
        minArcs = findMinimums(arcs[i])
        #print("ARCS!!!!!!!!!!!!!!!!!!!!")
        #print(arcs[i])
        for j in minArcs:
            arcs[i][(minArcs[j][0], j)] = 0
        #print(arcs[i])
        #print("ARCS!!!!!!!!!!!!!!!!!!!!")
        #print(arcs[i])
        cyclegraph = defaultdict(list)
        for j in arcs[i]:
            cyclegraph[j[0]].append(j[1])
        for j in temp_nodes:
            cyclegraph[j] += []
        #print("ARCS!!!!!!!!!!!!!!!!!!!!")
        #print(arcs[i])
        #print(cyclegraph)
        cyclegraph = dict(cyclegraph)
        cycles = []
        for node in cyclegraph:
            for path in dfs(cyclegraph, node, node):
                cycles.append([node] + path)
        # find 0-cost cycle
        #print("ARCS!!!!!!!!!!!!!!!!!!!!")
        #print(arcs[i])
        chosen_cycle = []
        for cycle in cycles:
            weight = 0
            for j in range(len(cycle)-1):
                weight += arcs[i][(cycle[j], cycle[j+1])]
            if weight == 0.0:
                chosen_cycle = cycle
                break
        #print("ARCS!!!!!!!!!!!!!!!!!!!!")
        #print(arcs[i])
        #print(chosen_cycle)
        temp_arc = dict(arcs[i])
        ancestors = defaultdict(list)
        newnodes = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','X','Y','Z']
        #print("ARCS!!!!!!!!!!!!!!!!!!!!")
        #print(arcs[i])
        while len(chosen_cycle) != 0:
            #print(ancestors)
            #constrict it
            #print(temp_arc)
            new = newnodes.pop()
            ancestors[new] = chosen_cycle
            for j in range(len(chosen_cycle) - 1):
                for ji in range(len(chosen_cycle) - 1):
                    try:
                        del temp_arc[(chosen_cycle[j],chosen_cycle[ji])]
                    except KeyError:
                        pass
            #print("ARCS!!!!!!!!!!!!!!!!!!!!")
            #print(arcs[i])
            #print(temp_arc)
            new_temp_arc = defaultdict(float)
            for j in temp_arc:
                if j[0] in chosen_cycle:
                    new_temp_arc[(new,j[1])] = temp_arc[j]
                elif j[1] in chosen_cycle:
                    new_temp_arc[(j[0], new)] = temp_arc[j]
                else:
                    new_temp_arc[j] = temp_arc[j]
            #print(temp_arc)
            temp_arc = dict(new_temp_arc)
            #print(temp_arc)
            #print(ancestors)
            #print("ARCS!!!!!!!!!!!!!!!!!!!!")
            #print(arcs[i])
            temp_nodes = set()
            for n in arcs[i]:
                temp_nodes.add(n[0])
                temp_nodes.add(n[1])
            minArcs = findMinimums(temp_arc)
            #print(minArcs)
            for j in minArcs:
                temp_arc[(minArcs[j][0], j)] = 0
            #print(arcs[i])
            cyclegraph = defaultdict(list)
            for j in temp_arc:
                cyclegraph[j[0]].append(j[1])
            for j in temp_nodes:
                cyclegraph[j] += []
            #print(cyclegraph)
            #print(ancestors)
            for j in ancestors:
                cyclegraph[j] += []
            cyclegraph = dict(cyclegraph)
            cycles = []
            for node in cyclegraph:
                for path in dfs(cyclegraph, node, node):
                    cycles.append([node] + path)
            #print("ARCS!!!!!!!!!!!!!!!!!!!!")
            #print(arcs[i])
            # find 0-cost cycle
            chosen_cycle = []
            for cycle in cycles:
                weight = 0
                for j in range(len(cycle) - 1):
                    weight += temp_arc[(cycle[j], cycle[j + 1])]
                if weight == 0.0:
                    chosen_cycle = cycle
                    break
            #print(chosen_cycle)
        #print("ARCS!!!!!!!!!!!!!!!!!!!!")
        #print(arcs[i])
        arbor = findMinimums(temp_arc)
        #print(arbor)
        #print("GOOD UP UNTIL HERE")
        #print(ancestors)
        # START UNBREAKING THE GRAPH (remove back-edges)
        new_arbor = defaultdict(tuple)
        #for k in ancestors:
        ## ATM REALLY ROBUST APPROACH, COULD BE MORE CORRECT AND ELEGANT
        k = list(ancestors)#
        #print(k)
        #print(set(list(arbor)).intersection(set(k)))
        helper = 1
        #print(ancestors)
        if len(k) > 0:
            for test in sorted(k):
                #print(test)
                for j in list(arbor):
                    if j == test:
                        for l in range(len(ancestors[j])-2):
                            new_arbor[ancestors[j][l]] = (ancestors[j][l+1],0)
                        new_arbor[ancestors[j][-2]] = arbor[j]
                    elif arbor[j][0] == test:
                        new_arbor[j] = (ancestors[arbor[j][0]][0],0)
                        for l in range(1,len(ancestors[arbor[j][0]])-2):
                            new_arbor[ancestors[arbor[j][0]][l-1]] = (ancestors[arbor[j][0]][l],0)
                    else:
                        new_arbor[j] = arbor[j]
                arbor = dict(new_arbor)
        else:
            new_arbor = arbor
        #print(new_arbor)
        # Finalise the result
        #print(nodes)
        #print(new_arbor)
        #print(arcs[i])
        temp_nodes = set()
        for n in arcs[i]:
            temp_nodes.add(n[0])
            temp_nodes.add(n[1])
        temp_nodes.remove('0')

        #print(arcs[i])
        #print(temp_nodes)
        for s in temp_nodes:
            #print(s)
            #print(new_arbor[s])
            a = list(list(nodes[i][s])[0])
            a[0] = int(s)
            a[6] = int(new_arbor[s][0])
            if a[6] == 0:
                a[7] = 'root'
            elif a[6] != 0 and a[7] == 'root':
                a[7] = 'nsubj'
            finalnodes[i].append(a)

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