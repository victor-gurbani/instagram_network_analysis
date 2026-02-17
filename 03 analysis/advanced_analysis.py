import argparse
import json
import pprint
from helper_functions import *


def advanced_analysis(config):
    my_name = config.username
    include_me = config.include_me
    input_txt_file = config.input_txt_file

    G_directed = create_graph_from_txt(my_name, include_me, input_txt_file)
    G_undirected = create_undirected_graph_from_txt(my_name, include_me, input_txt_file)

    print(
        f"Network: {G_directed.number_of_nodes()} nodes, {G_directed.number_of_edges()} directed edges"
    )
    print(
        f"Undirected: {G_undirected.number_of_nodes()} nodes, {G_undirected.number_of_edges()} edges"
    )
    print("=" * 60)

    # --- 1. Clustering Coefficient (The "Clique" Index) ---
    print('\n### 1. Clustering Coefficient (The "Clique" Index)')
    print("-" * 50)

    clustering_coefficients = nx.clustering(G_undirected)
    avg_clustering = nx.average_clustering(G_undirected)
    print(f"Average clustering coefficient: {avg_clustering:.4f}")
    print("  → 1.0 = everyone's friends are friends with each other")
    print("  → 0.0 = nobody's friends know each other")

    top_clustered = sort_and_small_dict(clustering_coefficients, 10)
    bottom_clustered = reverse_sort_and_small_dict(clustering_coefficients, 10)

    print("\nTop 10 most tightly clustered (part of cliques):")
    for name, score in top_clustered:
        print(f"  {name}: {score:.4f}")

    print("\nTop 10 connectors (bridge diverse groups):")
    for name, score in bottom_clustered:
        print(f"  {name}: {score:.4f}")

    # --- 2. Reciprocity (The "Realness" Ratio) ---
    print('\n\n### 2. Reciprocity (The "Realness" Ratio)')
    print("-" * 50)

    overall_reciprocity = nx.reciprocity(G_directed)
    print(f"Overall network reciprocity: {overall_reciprocity:.4f}")
    print(f"  → {overall_reciprocity * 100:.1f}% of connections are mutual follows")
    print("  → High = genuine friendships, Low = celebrity/fan dynamic")

    node_reciprocity = {}
    for node in G_directed.nodes():
        successors = set(G_directed.successors(node))
        predecessors = set(G_directed.predecessors(node))
        total_connections = len(successors | predecessors)
        if total_connections > 0:
            mutual = len(successors & predecessors)
            node_reciprocity[node] = mutual / total_connections
        else:
            node_reciprocity[node] = 0.0

    nodes_with_connections = {
        k: v for k, v in node_reciprocity.items() if G_directed.degree(k) > 0
    }
    if nodes_with_connections:
        top_reciprocal = sort_and_small_dict(nodes_with_connections, 10)
        bottom_reciprocal = reverse_sort_and_small_dict(nodes_with_connections, 10)

        print("\nTop 10 most reciprocal (mutual friendships):")
        for name, score in top_reciprocal:
            print(f"  {name}: {score:.4f}")

        print("\nTop 10 least reciprocal (one-way connections):")
        for name, score in bottom_reciprocal:
            print(f"  {name}: {score:.4f}")

    # --- 3. Degree Assortativity (The "Snob" Index) ---
    print('\n\n### 3. Degree Assortativity (The "Snob" Index)')
    print("-" * 50)

    try:
        assortativity = nx.degree_assortativity_coefficient(G_directed)
        print(f"Degree assortativity coefficient: {assortativity:.4f}")
        if assortativity > 0:
            print("  → Positive: popular people connect with popular people")
        elif assortativity < 0:
            print(
                "  → Negative: popular people connect with less popular people (hub-and-spoke)"
            )
        else:
            print("  → Neutral: no correlation between node degrees")
    except Exception as e:
        print(f"  Could not compute assortativity: {e}")

    # --- 4. K-Core Decomposition (The "Inner Circle") ---
    print('\n\n### 4. K-Core Decomposition (The "Inner Circle")')
    print("-" * 50)

    core_numbers = nx.core_number(G_undirected)
    max_k = max(core_numbers.values()) if core_numbers else 0
    print(f"Maximum k-core: {max_k}")

    k_core_graph = nx.k_core(G_undirected)
    print(f"Innermost core has {k_core_graph.number_of_nodes()} members:")

    inner_circle = sorted(k_core_graph.nodes())
    for member in inner_circle:
        print(f"  - {member}")

    print(f"\nK-core distribution:")
    core_distribution = collections.Counter(core_numbers.values())
    for k in sorted(core_distribution.keys()):
        print(f"  {k}-core: {core_distribution[k]} nodes")

    # --- 5. Diameter & Average Path Length (The "Small World" Check) ---
    print('\n\n### 5. Diameter & Average Path Length (The "Small World" Check)')
    print("-" * 50)

    if nx.is_connected(G_undirected):
        diameter = nx.diameter(G_undirected)
        avg_path_length = nx.average_shortest_path_length(G_undirected)
        print(f"Diameter: {diameter}")
        print(f"Average shortest path length: {avg_path_length:.4f}")
        print(f"  → Information travels across your entire network in ≤{diameter} hops")
    else:
        components = list(nx.connected_components(G_undirected))
        largest_cc = max(components, key=len)
        G_largest = G_undirected.subgraph(largest_cc).copy()

        print(f"Network is NOT fully connected ({len(components)} components)")
        print(
            f"Largest component: {len(largest_cc)} / {G_undirected.number_of_nodes()} nodes "
            f"({100 * len(largest_cc) / G_undirected.number_of_nodes():.1f}%)"
        )

        diameter = nx.diameter(G_largest)
        avg_path_length = nx.average_shortest_path_length(G_largest)
        print(f"\nLargest component diameter: {diameter}")
        print(f"Largest component avg path length: {avg_path_length:.4f}")
        print(f"  → Within the main group, info travels in ≤{diameter} hops")

        print(f"\nAll component sizes:")
        component_sizes = sorted([len(c) for c in components], reverse=True)
        for i, size in enumerate(component_sizes):
            print(f"  Component {i + 1}: {size} nodes")

    print("\n" + "=" * 60)
    print("Advanced analysis complete.")


if __name__ == "__main__":
    with open("../config.json") as config_file:
        conf = json.load(config_file)
    default_username = conf["username"]

    parser = argparse.ArgumentParser(
        description="Advanced network analysis: clustering, reciprocity, assortativity, k-core, diameter"
    )

    parser.add_argument(
        "--username",
        type=str,
        default=default_username,
        help="Username (default from ../config.json)",
    )
    parser.add_argument(
        "--input_txt_file",
        type=str,
        default="relations.txt",
        help="Input text file (default: relations.txt)",
    )
    parser.add_argument(
        "--include_me",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        help="Include current user in analysis (default: False)",
    )

    config = parser.parse_args()
    advanced_analysis(config)
