#!/usr/bin/env python3
"""
Chinese Postman Problem Solver

This module implements the Chinese Postman Problem (CPP) algorithm to find the shortest
closed path that traverses every edge of a graph at least once.

Author: Ralf Kistner
Modified for Python 3.8+ and NetworkX 2.8+
"""

import os
import sys
import tempfile
import subprocess
import csv

import networkx as nx
import xml.dom.minidom as minidom


def pairs(lst, circular=False):
    """
    Loop through all pairs of successive items in a list.

    Args:
        lst: List of items.
        circular: If True, include the pair (last, first).

    Yields:
        Tuples of successive items.

    Examples:
        >>> list(pairs([1, 2, 3, 4]))
        [(1, 2), (2, 3), (3, 4)]
        >>> list(pairs([1, 2, 3, 4], circular=True))
        [(1, 2), (2, 3), (3, 4), (4, 1)]
    """
    i = iter(lst)
    first = prev = item = next(i)
    for item in i:
        yield prev, item
        prev = item
    if circular:
        yield item, first


def import_csv_graph(file):
    """
    Import a graph from a CSV file.

    Args:
        file: File object or path to CSV file.

    Returns:
        nx.Graph: Graph with nodes and edges annotated with weights and coordinates.

    Notes:
        Each row must have the following columns (in order):
        - Start node ID
        - End node ID
        - Length in meters
        - Edge name or ID
        - Start longitude
        - Start latitude
        - End longitude
        - End latitude
        
        The first row is assumed to be a header and is skipped if it contains
        non-numeric values in the first few columns.
    """
    reader = csv.reader(file)
    graph = nx.Graph()
    
    for row_number, row in enumerate(reader):
        # Skip empty rows
        if not row:
            continue
            
        try:
            # Try to parse the first numeric column (length)
            # If this fails, assume it's a header row
            float(row[2])
        except (ValueError, IndexError):
            # Skip header row or invalid rows
            continue
            
        try:
            start_node = row[0]
            end_node = row[1]
            length = float(row[2])
            id = row[3]
            start_lon, start_lat, end_lon, end_lat = map(float, row[4:8])
            graph.add_edge(start_node, end_node, weight=length, id=id, label=id)

            # Store GPS coordinates in node attributes
            graph.nodes[start_node]['longitude'] = start_lon
            graph.nodes[start_node]['latitude'] = start_lat
            graph.nodes[end_node]['longitude'] = end_lon
            graph.nodes[end_node]['latitude'] = end_lat
        except (ValueError, IndexError) as e:
            print(f"Skipping input row {row_number + 1}: {e}")

    return graph


def specify_positions(graph):
    """
    Assign positions to nodes for graph visualization.

    Args:
        graph: nx.Graph with 'latitude' and 'longitude' attributes.
    """
    nodes = list(graph.nodes(data=True))
    if not nodes:
        return
    
    lat_min = min([data['latitude'] for _, data in nodes])
    lat_max = max([data['latitude'] for _, data in nodes])
    lon_min = min([data['longitude'] for _, data in nodes])
    lon_max = max([data['longitude'] for _, data in nodes])

    for node, data in nodes:
        latitude = data['latitude']
        longitude = data['longitude']
        y = (latitude - lat_min) / (lat_max - lat_min) * 1000
        x = (longitude - lon_min) / (lon_max - lon_min) * 1000
        graph.nodes[node]['pos'] = f"{int(x)},{int(y)}"


def make_png(graph, path):
    """
    Generate a PNG image of the graph using Graphviz.

    Args:
        graph: nx.Graph to visualize.
        path: Output file path for the PNG image.
    """
    try:
        from networkx.drawing.nx_pydot import write_dot
    except ImportError:
        try:
            import pydot
            from networkx.drawing.nx_pydot import write_dot
        except ImportError:
            try:
                import pydotplus
                from networkx.drawing.nx_pydot import write_dot
            except ImportError:
                raise ImportError(
                    "To generate PNG images, install either pygraphviz, pydot, or pydotplus. "
                    "Also ensure Graphviz is installed on your system."
                )

    fd, dotfile = tempfile.mkstemp(prefix="graph", suffix=".dot")
    try:
        write_dot(graph, dotfile)
        subprocess.call(['neato', '-n2', '-Tpng', '-o', path, dotfile])
    finally:
        os.remove(dotfile)


def graph_components(graph):
    """
    Return connected components as subgraph copies, sorted by descending size (edge count).

    Args:
        graph: Input graph.

    Returns:
        List of nx.Graph: Connected components, largest first.
    """
    components = [graph.subgraph(c).copy() for c in nx.connected_components(graph)]
    components.sort(key=lambda c: c.size(), reverse=True)
    return components


def odd_graph(graph):
    """
    Construct a fully connected graph of odd-degree nodes with edge weights as shortest path distances.

    Args:
        graph: Input graph.

    Returns:
        nx.Graph: Complete graph of odd-degree nodes with negative weights (for max_weight_matching).

    Notes:
        The edge weights are negative because max_weight_matching finds the maximum weight matching,
        but we want the minimum total distance.
    """
    result = nx.Graph()
    odd_nodes = [n for n in graph.nodes() if graph.degree(n) % 2 == 1]
    
    for i, u in enumerate(odd_nodes):
        # Calculate shortest paths from u to all other odd nodes
        paths = dict(nx.shortest_path(graph, source=u, weight='weight'))
        lengths = dict(nx.shortest_path_length(graph, source=u, weight='weight'))
        
        for j, v in enumerate(odd_nodes):
            if i >= j:
                continue  # Avoid duplicate edges
            
            # Add edge with negative weight (for max_weight_matching)
            result.add_edge(u, v, weight=-lengths[v], path=paths[v])

    return result


def as_gpx(graph, track_list, name=None):
    """
    Convert a list of tracks to GPX format.

    Args:
        graph: nx.Graph with 'latitude' and 'longitude' attributes.
        track_list: List of tracks, where each track is a dict with 'points' (list of node IDs).
        name: Optional name for the GPX file.

    Returns:
        str: GPX XML string.
    """
    doc = minidom.Document()
    root = doc.createElement("gpx")
    root.setAttribute("version", "1.0")
    doc.appendChild(root)

    if name:
        gpx_name = doc.createElement("name")
        gpx_name.appendChild(doc.createTextNode(name))
        root.appendChild(gpx_name)

    for i, track in enumerate(track_list):
        nr = i + 1
        track_name = track.get('name') or f"Track {nr}"
        trk = doc.createElement("trk")
        
        trk_name = doc.createElement("name")
        trk_name.appendChild(doc.createTextNode(track_name))
        trk.appendChild(trk_name)
        
        trk_number = doc.createElement("number")
        trk_number.appendChild(doc.createTextNode(str(nr)))
        trk.appendChild(trk_number)
        
        trkseg = doc.createElement("trkseg")

        for u in track['points']:
            node_data = graph.nodes[u]
            longitude = node_data.get('longitude')
            latitude = node_data.get('latitude')
            
            trkpt = doc.createElement("trkpt")
            trkpt.setAttribute("lat", str(latitude))
            trkpt.setAttribute("lon", str(longitude))
            
            ele = doc.createElement("ele")
            ele.appendChild(doc.createTextNode(str(u)))
            trkpt.appendChild(ele)
            
            trkseg.appendChild(trkpt)

        trk.appendChild(trkseg)
        root.appendChild(trk)

    return doc.toxml()


def write_csv(graph, nodes, out):
    """
    Write the path as a CSV file.

    Args:
        graph: nx.Graph with edge attributes.
        nodes: List of node IDs in the path.
        out: File object to write to.
    """
    writer = csv.writer(out)
    writer.writerow(["Start Node", "End Node", "Segment Length", "Segment ID", 
                     "Start Longitude", "Start Latitude", "End Longitude", "End Latitude"])
    
    for u, v in pairs(nodes, circular=False):
        edge_data = graph.edges[u, v]
        length = edge_data['weight']
        id = edge_data['id']
        
        start_latitude = graph.nodes[u].get('latitude')
        start_longitude = graph.nodes[u].get('longitude')
        end_latitude = graph.nodes[v].get('latitude')
        end_longitude = graph.nodes[v].get('longitude')
        
        writer.writerow([u, v, length, id, start_longitude, start_latitude, end_longitude, end_latitude])


def edge_sum(graph):
    """
    Calculate the total weight of all edges in the graph.

    Args:
        graph: nx.Graph with 'weight' attributes.

    Returns:
        float: Sum of all edge weights.
    """
    return sum(data['weight'] for _, _, data in graph.edges(data=True))


def matching_cost(graph, matching):
    """
    Calculate the total cost of a matching (sum of absolute weights).

    Args:
        graph: nx.Graph with 'weight' attributes.
        matching: Dict or set of edges representing the matching.

    Returns:
        float: Total cost of the matching.
    """
    cost = 0
    # In NetworkX >= 2.8, max_weight_matching returns a set of edges
    for u, v in matching:
        data = graph.edges[u, v]
        cost += abs(data['weight'])
    return cost


def find_matchings(graph, n=5):
    """
    Find the n best matchings for a graph.

    Args:
        graph: nx.Graph (typically the odd-degree graph).
        n: Number of matchings to find.

    Returns:
        List of tuples: (cost, matching) for each matching, sorted by cost.

    Notes:
        The best matching is guaranteed to be optimal. Subsequent matchings are estimates.
    """
    # Find the best matching
    best_matching = nx.max_weight_matching(graph, maxcardinality=True)
    matchings = [best_matching]

    # Try to find alternative matchings by removing edges from the best matching
    for u, v in best_matching:
        smaller_graph = graph.copy()
        smaller_graph.remove_edge(u, v)
        matching = nx.max_weight_matching(smaller_graph, maxcardinality=True)
        if matching:
            matchings.append(matching)

    # Calculate costs and sort
    matching_costs = [(matching_cost(graph, matching), matching) for matching in matchings]
    matching_costs.sort(key=lambda k: k[0])

    # Remove duplicates (matchings with the same cost)
    final_matchings = []
    last_cost = None
    for cost, matching in matching_costs:
        if cost == last_cost:
            continue
        last_cost = cost
        final_matchings.append((cost, matching))

    return final_matchings[:n]


def build_eulerian_graph(graph, odd, matching):
    """
    Build an Eulerian graph by duplicating edges along the shortest paths for matched pairs.

    Args:
        graph: Original graph.
        odd: Odd-degree graph (from odd_graph).
        matching: Matching of odd-degree nodes.

    Returns:
        nx.MultiGraph: Eulerian graph with duplicated edges.
    """
    eulerian_graph = nx.MultiGraph(graph)

    for u, v in matching:
        edge = odd.edges[u, v]
        path = edge['path']  # Shortest path between u and v in the original graph

        # Add each segment in the path to the graph again
        for p, q in pairs(path):
            weight = graph.edges[p, q]['weight']
            eulerian_graph.add_edge(p, q, weight=weight)

    return eulerian_graph


def eulerian_circuit(graph):
    """
    Find an Eulerian circuit in the graph.

    Args:
        graph: Eulerian graph (all nodes have even degree).

    Returns:
        List: Sequence of nodes in the circuit, with the first and last node the same.
    """
    circuit = list(nx.eulerian_circuit(graph))
    nodes = []
    for u, v in circuit:
        nodes.append(u)
    # Close the loop
    if nodes:
        nodes.append(circuit[0][0])
    return nodes


def chinese_postman_paths(graph, n=5):
    """
    Find the n best Chinese Postman paths for a graph.

    Args:
        graph: Input graph.
        n: Number of paths to find.

    Returns:
        List of tuples: (eulerian_graph, nodes) for each path.
    """
    odd = odd_graph(graph)
    matchings = find_matchings(odd, n)

    paths = []
    for cost, matching in matchings[:n]:
        eulerian_graph = build_eulerian_graph(graph, odd, matching)
        nodes = eulerian_circuit(eulerian_graph)
        paths.append((eulerian_graph, nodes))
    
    return paths


def single_chinese_postman_path(graph):
    """
    Find the shortest Chinese Postman path for a graph.

    Args:
        graph: Input graph.

    Returns:
        Tuple: (eulerian_graph, nodes) for the optimal path.

    Notes:
        If V' (number of odd-degree nodes) is at least 10% of V (total nodes),
        the complexity is approximately O(V^3).
    """
    odd = odd_graph(graph)
    matching = nx.max_weight_matching(odd, maxcardinality=True)
    eulerian_graph = build_eulerian_graph(graph, odd, matching)
    nodes = eulerian_circuit(eulerian_graph)
    return eulerian_graph, nodes


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Solve the Chinese Postman Problem for a graph given as a CSV file."
    )
    parser.add_argument("input", help="Input CSV file", type=argparse.FileType('r'))
    parser.add_argument("--csv", help="CSV output file", type=argparse.FileType('w'))
    parser.add_argument("--gpx", help="GPX output file", type=argparse.FileType('w'))
    parser.add_argument("--png", help="PNG output file", type=argparse.FileType('wb'))
    args = parser.parse_args()

    graph = import_csv_graph(args.input)
    components = graph_components(graph)
    
    if not components:
        raise ValueError("No graph components found; check input file")

    # Only use the largest component
    component = components[0]

    paths = chinese_postman_paths(component, n=5)

    for eulerian_graph, nodes in paths:
        in_length = edge_sum(component) / 1000.0
        path_length = edge_sum(eulerian_graph) / 1000.0
        duplicate_length = path_length - in_length

        print(f"Total length of roads: {in_length:.3f} km")
        print(f"Total length of path: {path_length:.3f} km")
        print(f"Length of sections visited twice: {duplicate_length:.3f} km")
        print(f"Node sequence: {nodes}")
        print()

    eulerian_graph, nodes = paths[0]  # The best one

    if args.gpx:
        args.gpx.write(as_gpx(component, [{'points': nodes}]))

    if args.csv:
        write_csv(component, nodes, args.csv)

    if args.png:
        specify_positions(eulerian_graph)
        make_png(eulerian_graph, args.png.name)
