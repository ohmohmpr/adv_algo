import matplotlib.animation
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import shapely.plotting
from shapely import LineString

def plot_two_polys(polys1: shapely.Polygon, polys2: shapely.Polygon, title: str = "No title") -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)

    for poly in polys1:
        shapely.plotting.plot_polygon(poly, ax1)

    for poly in polys2:
        shapely.plotting.plot_polygon(poly, ax2)
    fig.suptitle("Set ID: " + str(title))



def plot_two_polys_with_tree(polys1: shapely.Polygon, polys2: shapely.Polygon, 
                             G1: nx.classes.graph.Graph, G2: nx.classes.graph.Graph,
                             title: str = "No title") -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)

    for node in G1.nodes:
        shapely.plotting.plot_points(G1.nodes[node]['poly'].centroid, ax1, markersize=4, label=node)
    for node in G2.nodes:
        shapely.plotting.plot_points(G2.nodes[node]['poly'].centroid, ax2, markersize=4, label=node)

    list_edges_G1 = list(nx.bfs_edges(G1, source=0))
    for pairs in list_edges_G1:
        source_node = [G1.nodes[pairs[0]]['poly'].centroid.x, G1.nodes[pairs[0]]['poly'].centroid.y]
        target_node = [G1.nodes[pairs[1]]['poly'].centroid.x, G1.nodes[pairs[1]]['poly'].centroid.y]
        edge = LineString([ source_node, target_node ])
        shapely.plotting.plot_line(edge, ax1, add_points=False, color='red', linewidth=1)
    list_edges_G2 = list(nx.bfs_edges(G2, source=0))
    for pairs in list_edges_G2:
        source_node = [G2.nodes[pairs[0]]['poly'].centroid.x, G2.nodes[pairs[0]]['poly'].centroid.y]
        target_node = [G2.nodes[pairs[1]]['poly'].centroid.x, G2.nodes[pairs[1]]['poly'].centroid.y]
        edge = LineString([ source_node, target_node ])
        shapely.plotting.plot_line(edge, ax2, add_points=False, color='red', linewidth=1)


    for poly in polys1:
        shapely.plotting.plot_polygon(poly, ax1)
    for poly in polys2:
        shapely.plotting.plot_polygon(poly, ax2)

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
    
    colors = "bgrcmykw"
    color_index = 0
    
    def update(frame):
        ax1.clear()
        ax2.clear()
        list_edges_G1 = list(nx.bfs_edges(G1, source=0, depth_limit=frame))
        list_edges_G2 = list(nx.bfs_edges(G2, source=0, depth_limit=frame))
    
        if frame == 0:
            shapely.plotting.plot_polygon(G1.nodes[0]['poly'], ax1, color=colors[0])
            shapely.plotting.plot_polygon(G2.nodes[0]['poly'], ax2, color=colors[0])
            fig.suptitle("Set ID: " + str(title) + " Original data")
        else:
            for edges in list_edges_G1:
                target_node = edges[1]
                polys1 = G1.nodes[target_node]['poly']
                shapely.plotting.plot_polygon(polys1, ax1, color=colors[target_node])
            for edges in list_edges_G2:
                target_node = edges[1]
                polys2 = G2.nodes[target_node]['poly']
                shapely.plotting.plot_polygon(polys2, ax2, color=colors[target_node])
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
