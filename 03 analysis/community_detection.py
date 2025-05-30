import argparse
import community as community

import json
from helper_functions import *
import pprint

# str2bool is imported from helper_functions via *

def community_detection(config):
    my_name = config.username
    include_me = config.include_me
    input_txt_file = config.input_txt_file
    input_json_file = config.input_json_file
    followers_file = config.followers_file # Get the new argument

    G = create_undirected_graph_from_txt(my_name, include_me, input_txt_file, followers_file_path=followers_file)

    # LOUVAIN METHOD
    partition_louvain = community.best_partition(G)
    size = float(len(set(partition_louvain.values())))
    pos = nx.spring_layout(G)
    count = 0.
    communities_louvain = []
    for com in set(partition_louvain.values()):
        count = count + 1.
        list_nodes = [nodes for nodes in partition_louvain.keys()
                      if partition_louvain[nodes] == com]
        communities_louvain.append(list_nodes)
        nx.draw_networkx_nodes(G, pos, list_nodes, node_size=20,
                               node_color=str(count / size))

    # GIRVAN NEWMAN
    communities_generator = nx.algorithms.community.girvan_newman(G)
    communities_newman = next(communities_generator)
    modularity_newman_new = nx.algorithms.community.modularity(G, communities_newman)

    modularity_newman_old = 0.00001
    count = 1
    while modularity_newman_new > modularity_newman_old:
        modularity_newman_old = modularity_newman_new
        communities_newman_final = communities_newman
        communities_newman = next(communities_generator)
        modularity_newman_new = nx.algorithms.community.modularity(G, communities_newman)
        count += 1

    partition_newman = {}
    for idx, cluster in enumerate(communities_newman_final):
        for profile in cluster:
            partition_newman[profile] = idx

    # Get new JSONs
    with open(input_json_file) as f:
        input_dict = json.load(f)

    json_with_groups_louvain = add_cluster_to_json(input_dict, partition_louvain)

    # Use configurable output path for Louvain JSON
    with open(config.output_louvain_json, 'w+') as outfile:
        json.dump(json_with_groups_louvain, outfile)
    print(f"Louvain community data saved to: {config.output_louvain_json}")

    json_with_groups_newman = add_cluster_to_json(input_dict, partition_newman)

    # Use configurable output path for Newman JSON
    with open(config.output_newman_json, 'w+') as outfile2:
        json.dump(json_with_groups_newman, outfile2)
    print(f"Girvan-Newman community data saved to: {config.output_newman_json}")

    print("\nPartition Louvain, " + str(len(communities_louvain)) + " clusters detected: ")
    pprint.pprint(communities_louvain)
    print("\n")
    print("Partition Girvan-Newman, " + str(len(communities_newman_final)) + " clusters detected: ")
    pprint.pprint(communities_newman)

    # Modularity score
    print("\n")
    print("Modularity score Louvain method: " + str(round(nx.algorithms.community.modularity(G, communities_louvain), 2)))
    print("Modularity score Girvan-Newman method at level " + str(count) + ": " + str(round(nx.algorithms.community.modularity(G, communities_newman_final), 2)))

if __name__ == '__main__':

    default_username = get_username_from_config()
    if default_username is None:
        # Fallback or error if username couldn't be loaded
        # For now, let's use a placeholder or raise an error
        # This behavior might need to be decided based on application's requirements
        print("Error: Username could not be loaded from config. Please check config.json.")
        # default_username = "fallback_user" # Or exit, or handle as appropriate
        # For the purpose of this refactor, we assume config is present and valid
        # If not, argparse will fail if default_username is None and --username is not provided.
        # Or, we can make the script exit if default_username is None.
        # For now, let's allow it to proceed and potentially fail at ArgumentParser if username is required.
        # A more robust solution would be to exit if default_username is None and it's critical.
        pass


    parser = argparse.ArgumentParser()

    # Input parameters with help and defaults
    parser.add_argument('--username', type=str, default=default_username, help='Username (default from config.json)')
    parser.add_argument('--input_txt_file', type=str, default='relations.txt', help='Input TXT file (default: relations.txt)')
    parser.add_argument('--input_json_file', type=str, default='relations.json', help='Input JSON file (default: relations.json)')
    parser.add_argument('--include_me', type=str2bool, default=False, help='Include yourself in the analysis (default: False)')
    parser.add_argument('--followers_file', type=str, default='followers.txt', help='Path to the file containing the list of followers (default: followers.txt)')
    parser.add_argument('--output_louvain_json', type=str, default='relations_louvain.json', help='Output JSON file for Louvain method (default: relations_louvain.json)')
    parser.add_argument('--output_newman_json', type=str, default='relations_newman.json', help='Output JSON file for Girvan-Newman method (default: relations_newman.json)')

    config = parser.parse_args()

    community_detection(config)
