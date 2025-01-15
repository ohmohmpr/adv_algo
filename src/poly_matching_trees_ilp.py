from gurobipy import Model, GRB, LinExpr
import networkx as nx

class Solution:
    def __init__(self):
        self.matches = []  # List of pairs of two arrays
        self.weights = []  # List of weights corresponding to the matches
        self.objective = 0.0  # Sum of all weights

    def add_match(self, osm_polys, atkis_polys, weight):
        """
        Add a match to the solution.

        Parameters:
        - osm_polys: List of integers representing OSM polygons.
        - atkis_polys: List of integers representing ATKIS polygons.
        - weight: Float representing the weight of the match.
        """
        self.matches.append((osm_polys, atkis_polys))
        self.weights.append(weight)
        self.objective += weight


def solve_ilp_trees(g, tree_osm, tree_atkis, num_osm_polys, num_atkis_polys, solution):
    """
    Solves an ILP defined by g and the two trees (tree_osm, tree_atkis), both directed from leaf to root.
    
    Parameters:
    - g: A networkx undirected graph with a boolean "referenced_map" attribute per node and a "weight" attribute per edge 
      as well as an array 'referenced polys' with the polygon IDs of the represented polygons in the respective map.
    - tree_osm: A networkx directed graph with attributes 'referenced_polys' and 'vertex_id_in_g' per node.
    - tree_atkis: A networkx directed graph with attributes 'referenced_polys' and 'vertex_id_in_g' per node.
    - num_osm_polys: Number of OSM polygons.
    - num_atkis_polys: Number of ATKIS polygons.
    - solution: An object of the `Solution` class to store matches.
    """
    # try:
    # Initialize the Gurobi environment
    model = Model("TreeConstrainedILP")

    # Restrict Gurobi to 1 thread per process
    model.setParam(GRB.Param.Threads, 1)

    # Deactivate console logging
    model.setParam("LogToConsole", 0)

    # Create variables per edge in g
    variables = []
    weights = []
    var_adj_osm_v = {v: [] for v in g.nodes}
    var_adj_atkis_v = {v: [] for v in g.nodes}
    sources = []
    targets = []
    
   
    for u, v, data in g.edges(data=True):
        # Ensure variables are added only once for undirected edges (left side to right side of the bipartite graph)
        if not g.nodes[u]['referenced_map'] and g.nodes[v]['referenced_map']:
            # -------> EDIT  ------->
            # print("Ensure variables are added only once for undirected edges")
            # <------- EDIT  <-------
            edge_var = model.addVar(vtype=GRB.BINARY, name=f"edge_{u}_{v}")
            variables.append(edge_var)
            weights.append(data['weight'])

            # Track variables for constraints
            var_adj_osm_v[u].append(edge_var)
            var_adj_atkis_v[v].append(edge_var)

            sources.append(u)
            targets.append(v)


    # Build the target function (maximize the sum of weighted edges)
    target_func = LinExpr(weights, variables)
    model.setObjective(target_func, GRB.MAXIMIZE)

    # Add legality constraints
    for map_switch in [False, True]:
        num_polys = num_osm_polys if not map_switch else num_atkis_polys
        adjacent_edges = var_adj_osm_v if not map_switch else var_adj_atkis_v

        tree = tree_osm if not map_switch else tree_atkis

        for i in range(num_polys):
            # -------> EDIT  ------->
            # for v, data in tree.nodes(data=True):
            #   print(v, data['vertex_id_in_g'], i)
            # <------- EDIT  <-------
            referring_vertices = [
                # data['vertex_id_in_g']
                # -------> EDIT  ------->
                data['referenced_polys']
                # <------- EDIT  <-------
                for v, data in tree.nodes(data=True)
                if 'referenced_polys' in data and i in data['referenced_polys']
            ]
          
            # -------> EDIT  ------->
            # print(referring_vertices)
            # <------- EDIT  <-------

            if referring_vertices:
                constr_expr = LinExpr()
                for rv in referring_vertices:
                    for adj_edge in adjacent_edges[rv]:
                        constr_expr.addTerms(1, adj_edge)
                model.addLConstr(constr_expr, GRB.LESS_EQUAL, 1.0)

    # Optimize the model
    model.optimize()

    # Retrieve solution: for each selected edge, add it to the solution
    matches_added = 0
    for i, var in enumerate(variables):
        # print(i, var)
        if var.x == 1.0:
            # Add the match to the solution
            solution.add_match(
                g.nodes[sources[i]]['referenced_polys'],
                g.nodes[targets[i]]['referenced_polys'],
                g[sources[i]][targets[i]]['weight']
            )
            matches_added += 1

    # except Exception as e:
    #     print(f"Exception during optimization: {e}")