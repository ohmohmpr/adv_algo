import matplotlib.animation
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import shapely.plotting
from shapely import LineString
from typing import List, Tuple, Dict

def plot_two_polys(polys1: shapely.Polygon, polys2: shapely.Polygon, title: str = "No title") -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)

    for poly in polys1:
        shapely.plotting.plot_polygon(poly, ax1)

    for poly in polys2:
        shapely.plotting.plot_polygon(poly, ax2)
    fig.suptitle("Set ID: " + str(title))


def unpack_poly(polys: List, poly_left_list: List[shapely.Polygon]) -> shapely.Polygon:
    poly_left = None
    for i in poly_left_list:
        if poly_left == None:
            poly_left = polys[i]
        else:
            poly_left = poly_left | polys[i]

    return poly_left

    for i, poly_left_list in polys_kv.items():

                poly_left  = unpack_poly(polys, poly_left_list['referenced_polys'])


def plot_two_polys_with_tree(polys1: shapely.Polygon, polys2: shapely.Polygon, 
                             G1: nx.classes.graph.Graph, G2: nx.classes.graph.Graph,
                             title: str = "No title") -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)

    for node in G1.nodes:
        poly1 = unpack_poly(polys1, G1.nodes[node]['referenced_polys'])
        shapely.plotting.plot_points(poly1.centroid, ax1, markersize=4, label=node)
    for node in G2.nodes:
        poly2 = unpack_poly(polys2, G2.nodes[node]['referenced_polys'])
        shapely.plotting.plot_points(poly2.centroid, ax2, markersize=4, label=node)

    if G1.number_of_nodes() != 0:
      list_edges_G1 = list(nx.bfs_edges(G1, source=G1.number_of_nodes()-1, reverse=True))
  
      for pairs in list_edges_G1:
          poly_s = unpack_poly(polys1, G1.nodes[pairs[0]]['referenced_polys'])
          poly_t = unpack_poly(polys1, G1.nodes[pairs[1]]['referenced_polys'])
          source_node = [poly_s.centroid.x, poly_s.centroid.y]
          target_node = [poly_t.centroid.x, poly_t.centroid.y]
          edge = LineString([ source_node, target_node ])
          shapely.plotting.plot_line(edge, ax1, add_points=False, color='red', linewidth=1)

    if G2.number_of_nodes() != 0:
      list_edges_G2 = list(nx.bfs_edges(G2, source=G2.number_of_nodes()-1, reverse=True))
      for pairs in list_edges_G2:
          poly_s = unpack_poly(polys2, G2.nodes[pairs[0]]['referenced_polys'])
          poly_t = unpack_poly(polys2, G2.nodes[pairs[1]]['referenced_polys'])
          source_node = [poly_s.centroid.x, poly_s.centroid.y]
          target_node = [poly_t.centroid.x, poly_t.centroid.y]
          edge = LineString([ source_node, target_node ])
          shapely.plotting.plot_line(edge, ax2, add_points=False, color='red', linewidth=1)

    for poly in polys1:
        shapely.plotting.plot_polygon(poly, ax1, add_points=False)
    for poly in polys2:
        shapely.plotting.plot_polygon(poly, ax2, add_points=False)

    ax1.legend()
    ax2.legend()
    fig.suptitle("Set ID: " + str(title))



def plot_ani(polys1: shapely.Polygon, polys2: shapely.Polygon, 
             G1: nx.classes.graph.Graph, G2: nx.classes.graph.Graph,
             title: str = "No title"):

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)
    
    for poly in polys1:
        shapely.plotting.plot_polygon(poly, ax1)
    
    for poly in polys2:
        shapely.plotting.plot_polygon(poly, ax2)

    fig.suptitle("Set ID: " + str(title) + "Original data")
    
    colors = "bgrcmykwbgrcmykwbgrcmykwbgrcmykwbgrcmykwbgrcmykwbgrcmykwbgrcmykwbgrcmykwbgrcmykwbgrcmykwbgrcmykw"
    color_index = 0
    
    def update(frame):
        ax1.clear()
        ax2.clear()
        if G1.number_of_nodes() != 0:
          list_edges_G1 = list(nx.bfs_edges(G1, source=G1.number_of_nodes()-1, reverse=True))
          
        if G2.number_of_nodes() != 0:
          list_edges_G2 = list(nx.bfs_edges(G2, source=G2.number_of_nodes()-1, reverse=True))
          
        if frame == 0:
            root_node_G1 = list_edges_G1[0][0]
            root_node_G2 = list_edges_G2[0][0]
          
            poly_G1 = unpack_poly(polys1, G1.nodes[root_node_G1]['referenced_polys'])
            poly_G2 = unpack_poly(polys2, G2.nodes[root_node_G2]['referenced_polys'])
          
            shapely.plotting.plot_polygon(poly_G1, ax1, color=colors[0])
            shapely.plotting.plot_polygon(poly_G2, ax2, color=colors[0])
            fig.suptitle("Set ID: " + str(title) + ", depth: " + str(frame))
        else:
            for edges in list_edges_G1:
                target_node = edges[1]
                poly_G1 = unpack_poly(polys1, G1.nodes[target_node]['referenced_polys'])
                shapely.plotting.plot_polygon(poly_G1, ax1, color=colors[target_node])
            for edges in list_edges_G2:
                target_node = edges[1]
                poly_G2 = unpack_poly(polys2, G2.nodes[target_node]['referenced_polys'])
                shapely.plotting.plot_polygon(poly_G2, ax2, color=colors[target_node])
            fig.suptitle("Set ID: " + str(title) + ", depth: " + str(frame))
          
        if len(list_edges_G1) == 0:
            shapely.plotting.plot_polygon(G1.nodes[0]['poly'], ax1, color=colors[0])
        if len(list_edges_G2) == 0:
            shapely.plotting.plot_polygon(G2.nodes[0]['poly'], ax2, color=colors[0])
          
        
        return ax1, ax2
    
    frame_limit = len(G1) if len(G1)>len(G2) else len(G2)
    
    ani = matplotlib.animation.FuncAnimation(fig=fig, func=update, frames=frame_limit, interval=400);

    from IPython.display import HTML
    return HTML(ani.to_jshtml())
