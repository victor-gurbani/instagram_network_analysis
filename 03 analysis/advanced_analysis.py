import argparse
import json
import pprint
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from helper_functions import *


def advanced_analysis(config):
    my_name = config.username
    include_me = config.include_me
    input_txt_file = config.input_txt_file

    G_directed = create_graph_from_txt(my_name, include_me, input_txt_file)
    G_undirected = create_undirected_graph_from_txt(my_name, include_me, input_txt_file)

    table_data_columns = []
    column_labels = []

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

    num_top = min(max(1, int(len(G_undirected) * 0.05)), 20)
    top_clustered = sort_and_small_dict(clustering_coefficients, num_top)

    # Bottom: Low-clustering nodes that aren't zero (connectors)
    non_zero_clustering = {k: v for k, v in clustering_coefficients.items() if v > 0}
    bottom_clustered = reverse_sort_and_small_dict(non_zero_clustering, 10)

    bottom_clustered_absolute = reverse_sort_and_small_dict(clustering_coefficients, 5)

    print(f"\nTop {num_top} most tightly clustered (part of cliques):")
    for name, score in top_clustered:
        print(f"  {name}: {score:.4f}")

    print("\nTop 10 connectors (low score > 0, bridge diverse groups):")
    for name, score in bottom_clustered:
        print(f"  {name}: {score:.4f}")

    print("\nTop 5 lowest clustering (including 0):")
    for name, score in bottom_clustered_absolute:
        print(f"  {name}: {score:.4f}")

    sorted_top_clust = sort_and_small_dict(clustering_coefficients, 8)
    sorted_bottom_clust = reverse_sort_and_small_dict(clustering_coefficients, 8)
    table_data_columns.append(
        centrality_to_str_arr(sorted_top_clust)
        + centrality_to_str_arr(sorted_bottom_clust)
    )
    column_labels.append("Clustering Coeff")

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
        num_top_rec = min(max(1, int(len(G_directed) * 0.05)), 20)
        top_reciprocal = sort_and_small_dict(nodes_with_connections, num_top_rec)

        non_zero_reciprocity = {
            k: v for k, v in nodes_with_connections.items() if v > 0
        }
        bottom_reciprocal = reverse_sort_and_small_dict(non_zero_reciprocity, 10)

        bottom_reciprocal_absolute = reverse_sort_and_small_dict(
            nodes_with_connections, 5
        )

        print(f"\nTop {num_top_rec} most reciprocal (mutual friendships):")
        for name, score in top_reciprocal:
            print(f"  {name}: {score:.4f}")

        print("\nTop 10 least reciprocal (low score > 0, one-way connections):")
        for name, score in bottom_reciprocal:
            print(f"  {name}: {score:.4f}")

        print("\nTop 5 lowest reciprocity (including 0):")
        for name, score in bottom_reciprocal_absolute:
            print(f"  {name}: {score:.4f}")

    sorted_top_rec = sort_and_small_dict(nodes_with_connections, 8)
    sorted_bottom_rec = reverse_sort_and_small_dict(nodes_with_connections, 8)
    table_data_columns.append(
        centrality_to_str_arr(sorted_top_rec) + centrality_to_str_arr(sorted_bottom_rec)
    )
    column_labels.append("Reciprocity")

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

    sorted_top_kcore = sort_and_small_dict(core_numbers, 8)
    sorted_bottom_kcore = reverse_sort_and_small_dict(core_numbers, 8)
    table_data_columns.append(
        centrality_to_str_arr(sorted_top_kcore)
        + centrality_to_str_arr(sorted_bottom_kcore)
    )
    column_labels.append("K-Core")

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

    # --- 6. Export K-Core JSON ---
    print("\n\n### 6. Export K-Core JSON")
    print("-" * 50)

    try:
        with open(config.input_json_file, "r") as f:
            relations_data = json.load(f)

        kcore_groups = {}
        # We'll assign colors directly to ensure correct visualization
        # Max core = Red (#ff0000), Others = Grey (#cccccc)
        for node in G_undirected.nodes():
            if node in inner_circle:
                kcore_groups[node] = "#ff0000"
            else:
                kcore_groups[node] = "#cccccc"

        # Filter the original nodes to only include those present in our graph
        # And update their groups/colors
        original_nodes = relations_data.get("nodes", [])
        filtered_nodes = []
        for node_item in original_nodes:
            name = node_item.get("name")
            if name in kcore_groups:
                node_item["color"] = kcore_groups[name]
                # Keep original group or set to something neutral if needed,
                # but 'color' property takes precedence in the JS.

                k_val = core_numbers.get(name, 0)
                node_item["k_core"] = k_val
                node_item["group"] = k_val

                filtered_nodes.append(node_item)

        relations_data["nodes"] = filtered_nodes

        # Also filter links to only include edges where both nodes are in our filtered set
        valid_node_names = set(kcore_groups.keys())
        original_links = relations_data.get("links", [])
        # We need to map IDs to names to check link validity if links use IDs
        # Looking at relations.json, links usually use 'source' and 'target' which can be IDs or names.
        # If they are IDs, we need to map them back to names.
        id_to_name = {n["id"]: n["name"] for n in original_nodes}

        filtered_links = []
        for link in original_links:
            source = link.get("source")
            target = link.get("target")

            # Check if source/target are IDs or names
            source_name = id_to_name.get(source) if isinstance(source, int) else source
            target_name = id_to_name.get(target) if isinstance(target, int) else target

            if source_name in valid_node_names and target_name in valid_node_names:
                filtered_links.append(link)

        relations_data["links"] = filtered_links

        with open(config.output_kcore_json, "w") as f:
            json.dump(relations_data, f, indent=4)
        print(f"K-Core JSON exported to {config.output_kcore_json}")

    except Exception as e:
        print(f"Error exporting K-Core JSON: {e}")

    print("\nGenerating results table image...")
    fig, ax = plt.subplots()
    fig.patch.set_visible(False)
    ax.axis("off")
    ax.axis("tight")

    if table_data_columns:
        data_for_table = np.transpose(table_data_columns)
        table = ax.table(colLabels=column_labels, cellText=data_for_table, loc="center")
        for (row, col), cell in table.get_celld().items():
            if (row == 0) or (col == -1):
                cell.set_text_props(fontproperties=FontProperties(weight="bold"))

        output_image_path = "./advanced_analysis_results.png"
        fig.tight_layout()
        plt.savefig(output_image_path, dpi=300)
        print(f"Results image saved to {output_image_path}")
    else:
        print("No data to display in table.")

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
    parser.add_argument(
        "--input_json_file",
        type=str,
        default="relations.json",
        help="Input JSON file for K-core export (default: relations.json)",
    )
    parser.add_argument(
        "--output_kcore_json",
        type=str,
        default="relations_kcore.json",
        help="Output JSON file for K-core visualization (default: relations_kcore.json)",
    )

    config = parser.parse_args()
    advanced_analysis(config)
