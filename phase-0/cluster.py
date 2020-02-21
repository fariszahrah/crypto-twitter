"""
Cluster data.
"""


'''
creates partitions using the community module
'''
import community
import pickle
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter


def partition(graph):
    '''
    takes a graph and returns a dict of nodes to their parition
    '''
    partition = community.best_partition(graph)
    return partition 


def graph_part(graph, part, filename):
    values = [part.get(node) for node in graph.nodes()]
    nx.draw_spring(graph, cmap = plt.get_cmap('jet'), node_color = values, node_size=30, with_labels=False)
    plt.savefig(filename, pad_inches=4)

def main():
    graph = nx.read_gpickle('./graph.gpickle')
    part = partition(graph)
    print('Graph partitioned into {0} communities'.format(len(set(part.values())))) 
    with open('partition.pickle', 'wb') as handle:
        pickle.dump(part, handle, protocol=pickle.HIGHEST_PROTOCOL)

    c = Counter(part.values())
    avg_sive = 0
    for i in c:
        avg_sive += (c[i]/len(c))
    print('Cluster average size: {0}'.format(round(avg_sive)))
    
    graph_part(graph,part,'network.png')



if __name__ == "__main__":
    main()
