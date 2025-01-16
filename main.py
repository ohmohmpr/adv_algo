# dev mode
import sys
from typing import List, Tuple
import matplotlib.pyplot as plt
import networkx as nx
import time
import copy

from src.file_reader import BinaryPolygonFileReader, test_load_module
from src.utils import plot_two_polys, plot_two_polys_with_tree, plot_ani
from src.poly_matching_trees_ilp import solve_ilp_trees, Solution
import shapely.plotting
import networkx as nx


def find_polys_smallest_dist_pairs(polys: List)-> tuple((List, List, List)):
    smallest_dist = float('inf')
    poly_i = None
    poly_j = None
    merged_i_j = None

    if len(polys) < 2:
        return poly_i, poly_j, merged_i_j 
        # raise ValueError("can not compared when the length is less than 2.")

    for i in range(len(polys)):
        j = i + 1
        for j in range(j, len(polys)):
            if polys[i].intersects(polys[j]):
                dist_centroid = polys[i].centroid.distance(polys[j].centroid)
                if dist_centroid < smallest_dist:
                    smallest_dist = dist_centroid
                    # print("dist", smallest_dist)
                    poly_i = polys[i]
                    poly_j = polys[j]
                    merged_i_j = polys[i] | polys[j]

    if merged_i_j == None and poly_i == None and poly_j == None:
        for i in range(len(polys)):
            j = i + 1
            for j in range(j, len(polys)):
                dist_centroid = polys[i].centroid.distance(polys[j].centroid)
                if dist_centroid < smallest_dist:
                    smallest_dist = dist_centroid
                    # print("dist", smallest_dist)
                    poly_i = polys[i]
                    poly_j = polys[j]
                    merged_i_j = polys[i] | polys[j]
    
    return poly_i, poly_j, merged_i_j
  
def find_geometry_Graph(G, poly):
    is_poly = False
    node_num = -1
    for node in G.nodes:
        p = G.nodes[node]['poly']
        if poly.equals_exact(p, 1e-6):
            is_poly = True
            return node, is_poly

    return None, is_poly

def add_node(G, poly_i, node_num):
    found_node_num, found_node = find_geometry_Graph(G, poly_i)
    if not found_node:
        node_num_i = node_num
        G.add_node(node_num_i, poly=poly_i, vertex_id_in_g=node_num_i, referenced_polys=[poly_i])
        node_num = node_num + 1
    else:
        node_num_i = found_node_num
        G.add_node(node_num_i, poly=poly_i, vertex_id_in_g=node_num_i, referenced_polys=[poly_i])

    return node_num_i, node_num

def algorithm_1(polys: List)-> nx.classes.graph.Graph:
    # it would be a good idea if we can use pointer here for G.
    G = nx.DiGraph()
    node_num = 1
    min_poly = 2
    if (len(polys) == 0):
        return G
    if (len(polys) == 1):
        G.add_node(0, poly=polys[0], vertex_id_in_g=0, referenced_polys=[polys[0]])
        return G

    while (len(polys) >= min_poly):
        poly_i, poly_j, merged_i_j = find_polys_smallest_dist_pairs(polys)

        polys.remove(poly_i)
        polys.remove(poly_j)
        polys.append(merged_i_j)

        node_num_i, node_num = add_node(G, poly_i, node_num)
        node_num_j, node_num = add_node(G, poly_j, node_num)

        if len(polys) == min_poly - 1:
            G.add_node(0, poly=merged_i_j, vertex_id_in_g=0, referenced_polys=[merged_i_j])
            G.add_edge(node_num_i, 0)
            G.add_edge(node_num_j, 0)
        else:
            node_num_i_j = node_num
            G.add_node(node_num_i_j, poly=merged_i_j, vertex_id_in_g=node_num_i_j, referenced_polys=[merged_i_j])
            G.add_edge(node_num_i, node_num_i_j)
            G.add_edge(node_num_j, node_num_i_j)
            node_num = node_num + 1

    return G


'''
    Name,            number of sets
    data_auerberg,              796
    data_dottendorf,            871
    data_duisdorf,             2127
    data_endenich,             1060
    data_zentrum,               160
'''
file_path = "data/data_endenich"
reader = BinaryPolygonFileReader(file_path)

# Save timestamp
from networkx.algorithms import bipartite
total_obj=0
start = time.time()
sol_algo1 = Solution()
lamda = 0.8

while True:
    try:
        set_id, polys1, polys2 = reader.read_next_set()
        G1 = algorithm_1(polys1)
        G2 = algorithm_1(polys2) 
        
        B_sol = nx.Graph()
    
        
        for G1_node_num in range(len(G1)):
            j = G1_node_num 
            for G2_node_num in range(len(G2)):
                B_sol.add_nodes_from([ (G1_node_num, {
                    'referenced_map': False, 
                    'referenced_polys': G1.nodes[G1_node_num]['referenced_polys']                     
                })  ], bipartite=0)
                B_sol.add_nodes_from([ (str(G2_node_num), {
                    'referenced_map': True, 
                    'referenced_polys': G2.nodes[G2_node_num]['referenced_polys']
                })  ], bipartite=1)
        
                polygon1 =  G1.nodes[G1_node_num]['poly']
                polygon2 =  G2.nodes[G2_node_num]['poly']
                
                intersect = polygon1.intersection(polygon2).area
                union = polygon1.union(polygon2).area
                iou = intersect / union
                
                B_sol.add_edges_from([ (G1_node_num, str(G2_node_num), {'weight': iou - lamda}) ]             )

        solve_ilp_trees(g=B_sol, tree_osm=G2, tree_atkis=G1, num_osm_polys=len(polys2), num_atkis_polys=len(polys1), solution=sol_algo1)
  
    except:
        if G1 == None or G2 == None:
            print("last set id: ",set_id)
            print("Error")
            break
        else:
            print("last set id: ",set_id)
            print("Finish")
            break
        break
# Save timestamp
end = time.time()

print(end - start)
print("total_obj", sol_algo1.objective)
print("total_matches", len(sol_algo1.matches))
# data_auerberg   time used: 1.345
# data_dottendorf time used: 1.086
# data_duisdorf   time used: 3.714
# data_endenich   time used: 4.603
# data_zentrum    time used: 18.042
