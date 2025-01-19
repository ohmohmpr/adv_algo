# dev mode
import sys
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt
import networkx as nx
import time
import copy

from src.file_reader import BinaryPolygonFileReader, test_load_module
from src.utils import plot_two_polys, plot_two_polys_with_tree, plot_ani
from src.poly_matching_trees_ilp import solve_ilp_trees, Solution, solve_ilp_trees_G2
import shapely.plotting
import networkx as nx


def unpack_poly(polys: List, poly_left_list: List[shapely.Polygon]) -> shapely.Polygon:
    poly_left = None
    for i in poly_left_list:
        if poly_left == None:
            poly_left = polys[i]
        else:
            poly_left = poly_left | polys[i]

    return poly_left

def compare(polys: List, polys_kv: Dict[int, List[shapely.Polygon]], intersect=True) -> Dict[int, List[shapely.Polygon]]:

    smallest_dist = float('inf')
    found_key_i = None
    found_key_j = None
    success = False
    
    for i, poly_left_list in polys_kv.items():
        for j, poly_right_list in polys_kv.items():
            # check sorted
            if i < j:
                # can optimize but left for checking.
                poly_left  = unpack_poly(polys, poly_left_list['referenced_polys'])
                poly_right = unpack_poly(polys, poly_right_list['referenced_polys'])

                if intersect == True:
                    if poly_left.intersects(poly_right):
                        dist_centroid = poly_left.centroid.distance(poly_right.centroid)
                        if dist_centroid < smallest_dist:
                            smallest_dist = dist_centroid
                            found_key_i = i
                            found_key_j = j
                            # print("i, j, dist_centroid", i, j, dist_centroid)
                            merged_i_j = poly_left | poly_right
                else:
                    dist_centroid = poly_left.centroid.distance(poly_right.centroid)
                    if dist_centroid < smallest_dist:
                        smallest_dist = dist_centroid
                        found_key_i = i
                        found_key_j = j
                        merged_i_j = poly_left | poly_right

    if found_key_i == None or found_key_j == None:
        return polys_kv, success
    else:
        polys_kv[j+1] = {}
        polys_kv[j+1]['child_left_node'] = found_key_i
        polys_kv[j+1]['child_right_node'] = found_key_j
        polys_kv[j+1]['referenced_polys'] = polys_kv[found_key_i]['referenced_polys'] + polys_kv[found_key_j]['referenced_polys']
        # print("ref", polys_kv[j+1]['referenced_polys'])
        polys_kv.pop(found_key_i)
        polys_kv.pop(found_key_j)
        success = True
    
    return polys_kv, success


def find_smallest_dist_pairs_polys(polys: List, polys_kv: Dict[int, List[shapely.Polygon]])-> Dict[int, List[shapely.Polygon]]:

    success = None

    if len(polys_kv) < 2:
        return polys_kv

    polys_kv, success = compare(polys, polys_kv)
    if success == False:
        polys_kv, success = compare(polys, polys_kv, intersect=False)

    return polys_kv

def algorithm_1(polys: List)-> nx.classes.graph.Graph:
    G = nx.DiGraph()
    polys_kv = {}

    current_vertex_id = 0
    
    if (len(polys) == 0):
        return G
    # if (len(polys) == 1):
    #     G.add_node(0, poly=polys[0], vertex_id_in_g=0, referenced_polys=[0])
    #     return G

    for i in range(len(polys)):
        polys_kv[i] = {}
        polys_kv[i]['referenced_polys'] = [i]
        polys_kv[i]['child_left_node'] = {}
        polys_kv[i]['child_right_node'] = {}
        G.add_node(i, vertex_id_in_g=i, referenced_polys=polys_kv[i]['referenced_polys'])
        current_vertex_id = current_vertex_id + 1        


    while (len(polys_kv) > 1):
        polys_kv = find_smallest_dist_pairs_polys(polys, polys_kv)

        G.add_node(current_vertex_id, vertex_id_in_g=current_vertex_id, referenced_polys=polys_kv[current_vertex_id]['referenced_polys'])
        G.add_edge(polys_kv[current_vertex_id]['child_left_node'], current_vertex_id)
        G.add_edge(polys_kv[current_vertex_id]['child_right_node'], current_vertex_id)
        current_vertex_id = current_vertex_id + 1

    return G


'''
    Name,            number of sets
    data_auerberg,              796       232
    data_dottendorf,            871       243
    data_duisdorf,             2127       520
    data_endenich,             1060       295
    data_zentrum,               160
'''
file_path = "data/data_endenich"
reader = BinaryPolygonFileReader(file_path)

# Save timestamp
from networkx.algorithms import bipartite
total_obj=0
start = time.time()
sol_algo1 = Solution()
lamda = 0.4
error = 0
set_id_error = []

while True:
    try:
        set_id, polys1, polys2 = reader.read_next_set()
        G1 = algorithm_1(polys1)
        G2 = algorithm_1(polys2)
        B_sol = nx.Graph()

        if len(G1) < len(G2):
            try:
                for G1_node_num in range(len(G1)):
                    for G2_node_num in range(len(G2)):
                        
                        B_sol.add_nodes_from([ (G1_node_num, {
                            'referenced_map': True, 
                            'referenced_polys': G1.nodes[G1_node_num]['referenced_polys']                     
                        })  ], bipartite=0)
                        B_sol.add_nodes_from([ (f"G2_{G2_node_num}", {
                            'referenced_map': False, 
                            'referenced_polys': G2.nodes[G2_node_num]['referenced_polys']
                        })  ], bipartite=1)
                    
                        polygon1 = unpack_poly(polys1, G1.nodes[G1_node_num]['referenced_polys'])
                        polygon2 = unpack_poly(polys2, G2.nodes[G2_node_num]['referenced_polys'])
                        
                        intersect = polygon1.intersection(polygon2).area
                        union = polygon1.union(polygon2).area
                        iou = intersect / union
                        
                        B_sol.add_edges_from([ (G1_node_num, f"G2_{G2_node_num}", {'weight': iou - lamda}) ])

                solve_ilp_trees_G2(g=B_sol, tree_osm=G1, tree_atkis=G2, num_osm_polys=len(polys1), num_atkis_polys=len(polys2), solution=sol_algo1)
            except:
                try:
                    for G1_node_num in range(len(G1)):
                        for G2_node_num in range(len(G2)):
                            
                            B_sol.add_nodes_from([ (G1_node_num, {
                                'referenced_map': True, 
                                'referenced_polys': G1.nodes[G1_node_num]['referenced_polys']                     
                            })  ], bipartite=0)
                            B_sol.add_nodes_from([ (f"G2_{G2_node_num}", {
                                'referenced_map': False, 
                                'referenced_polys': G2.nodes[G2_node_num]['referenced_polys']
                            })  ], bipartite=1)
                        
                            polygon1 = unpack_poly(polys1, G1.nodes[G1_node_num]['referenced_polys'])
                            polygon2 = unpack_poly(polys2, G2.nodes[G2_node_num]['referenced_polys'])
                            
                            intersect = polygon1.intersection(polygon2).area
                            union = polygon1.union(polygon2).area
                            iou = intersect / union
                            
                            B_sol.add_edges_from([ (G1_node_num, f"G2_{G2_node_num}", {'weight': iou - lamda}) ])

                    solve_ilp_trees(g=B_sol, tree_osm=G1, tree_atkis=G2, num_osm_polys=len(polys1), num_atkis_polys=len(polys2), solution=sol_algo1)
                except:
                    pass
        
        else:

            try:
                for G2_node_num in range(len(G2)):
                    for G1_node_num in range(len(G1)):
                        
                        B_sol.add_nodes_from([ (G1_node_num, {
                            'referenced_map': False, 
                            'referenced_polys': G1.nodes[G1_node_num]['referenced_polys']                     
                        })  ], bipartite=0)
                        B_sol.add_nodes_from([ (f"G2_{G2_node_num}", {
                            'referenced_map': True, 
                            'referenced_polys': G2.nodes[G2_node_num]['referenced_polys']
                        })  ], bipartite=1)
                    
                        polygon1 = unpack_poly(polys1, G1.nodes[G1_node_num]['referenced_polys'])
                        polygon2 = unpack_poly(polys2, G2.nodes[G2_node_num]['referenced_polys'])
                        
                        intersect = polygon1.intersection(polygon2).area
                        union = polygon1.union(polygon2).area
                        iou = intersect / union
                        
                        B_sol.add_edges_from([ (G1_node_num, f"G2_{G2_node_num}", {'weight': iou - lamda}) ])

                solve_ilp_trees_G2(g=B_sol, tree_osm=G1, tree_atkis=G2, num_osm_polys=len(polys1), num_atkis_polys=len(polys2), solution=sol_algo1)
            except:
                try:
                    for G2_node_num in range(len(G2)):
                        for G1_node_num in range(len(G1)):
                            
                            B_sol.add_nodes_from([ (G1_node_num, {
                                'referenced_map': False, 
                                'referenced_polys': G1.nodes[G1_node_num]['referenced_polys']                     
                            })  ], bipartite=0)
                            B_sol.add_nodes_from([ (G2_node_num, {
                                'referenced_map': True, 
                                'referenced_polys': G2.nodes[G2_node_num]['referenced_polys']
                            })  ], bipartite=1)
                        
                            polygon1 = unpack_poly(polys1, G1.nodes[G1_node_num]['referenced_polys'])
                            polygon2 = unpack_poly(polys2, G2.nodes[G2_node_num]['referenced_polys'])
                            
                            intersect = polygon1.intersection(polygon2).area
                            union = polygon1.union(polygon2).area
                            iou = intersect / union
                            
                            B_sol.add_edges_from([ (G1_node_num, G2_node_num, {'weight': iou - lamda}) ])

                    solve_ilp_trees(g=B_sol, tree_osm=G1, tree_atkis=G2, num_osm_polys=len(polys1), num_atkis_polys=len(polys2), solution=sol_algo1)
                except:
                    pass

        print("sol_algo1.objective", sol_algo1.objective)
        print("sol_algo1.matches", len(sol_algo1.matches))
        print("error", error)
        print("set_id_error", set_id_error)

    # except:
    #     if G1 == None or G2 == None:
    #         print("last set id: ",set_id)
    #         print("Error")
    #         break
    #     else:
    #         print("last set id: ",set_id)
    #         print("Finish")
    #         break
    #     break

    except Exception as e:
        if len(polys1) != 0 and len(polys2) != 0:
            error = error + 1
            set_id_error.append(set_id)
        pass
        # print("last set id: ",set_id)
        # print(f"Exception during optimization: {e}")
        # break

print("sol_algo1.objective", sol_algo1.objective)
print("sol_algo1.matches", sol_algo1.matches)

end = time.time()

print(end - start)
print("total_obj", sol_algo1.objective)
print("total_matches", len(sol_algo1.matches))
# data_auerberg   time used: 1.345
# data_dottendorf time used: 1.086
# data_duisdorf   time used: 3.714
# data_endenich   time used: 4.603
# data_zentrum    time used: 18.042
