import re
import networkx as nx
import argparse
import collections
import scipy.optimize
import json # Added for config loading
import os # Added for path manipulation for config loading


def fit_powerlaw(degrees, counts):
    if min(degrees) == 0:
        x = degrees[:-1]
        y = counts[:-1]
    else:
        x = degrees
        y = counts

    def powerlaw(x, a, b):
        return a * (x ** b)

    pars, covar = scipy.optimize.curve_fit(powerlaw, x, y)

    approx = []
    for elem in x:
        approx.append(powerlaw(elem, *pars))

    return (x, approx, pars)


def sort_and_small_dict(d, n):
    sorted_dict = collections.OrderedDict(sorted(d.items(), key=lambda x: -x[1]))
    firstnpairs = list(sorted_dict.items())[:n]
    return firstnpairs

def reverse_sort_and_small_dict(d, n):
    sorted_dict = collections.OrderedDict(sorted(d.items(), key=lambda x: x[1]))
    firstnpairs = list(sorted_dict.items())[:n]
    return firstnpairs[::-1]


def centrality_to_str_arr(centrality):
    str_arr = []
    for item in centrality:
        str_arr.append(item[0] + ' | ' + str(round(item[1], 2)))
    return str_arr


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def _create_graph_base(my_name, include_me, input_txt_file, graph_type, followers_file_path=None):
    nodes = set() # This will be our nodes_set
    edges = []
    G = graph_type()

    # Add nodes from followers_file_path first, if provided
    if followers_file_path:
        try:
            with open(followers_file_path, 'r') as f_followers:
                for line in f_followers:
                    follower_username = line.strip()
                    if follower_username: # Ensure not an empty line
                        nodes.add(follower_username)
            print(f"Successfully loaded {len(nodes)} initial nodes from {followers_file_path}")
        except FileNotFoundError:
            print(f"Warning: Followers file {followers_file_path} not found. Proceeding without it.")
        except Exception as e:
            print(f"Warning: Error reading {followers_file_path}: {e}. Proceeding without it.")

    # Add nodes and edges from the main input_txt_file
    try:
        with open(input_txt_file, 'r') as f:
            for line in f:
                accounts = line.split(" ")
                if len(accounts) < 2:
                    continue
                account_1 = accounts[0].strip()
                account_2 = accounts[1].strip()
                
                nodes.add(account_1) # Add account_1 to nodes
                nodes.add(account_2) # Add account_2 to nodes, ensure both are added before filtering

                if include_me:
                    edges.append([account_1, account_2])
                else:
                    if not (account_1 == my_name or account_2 == my_name):
                        edges.append([account_1, account_2])
    except FileNotFoundError:
        print(f"Error: Main input file {input_txt_file} not found. Cannot build graph.")
        return G # Return empty graph
    except Exception as e:
        print(f"Error: Could not read main input file {input_txt_file}: {e}. Cannot build graph.")
        return G # Return empty graph


    # Filter my_name from nodes set if not included
    if not include_me and my_name in nodes:
        nodes.remove(my_name)
    
    # Add my_name to nodes if it's included (ensures it's in the graph even if not in edges)
    # This also ensures 'my_name' is added even if it was only in followers_file and not relations.txt
    if include_me:
        nodes.add(my_name)

    for account in nodes:
        G.add_node(account)

    # Add edges, ensuring nodes in edges also exist if my_name was filtered from edges but not nodes
    for acc_1, acc_2 in edges:
        if include_me or (acc_1 != my_name and acc_2 != my_name):
             if acc_1 in G and acc_2 in G: # Ensure nodes exist in graph before adding edge
                G.add_edge(acc_1, acc_2)
    return G


def create_graph_from_txt(my_name, include_me, input_txt_file, followers_file_path=None): # Added followers_file_path to signature
    return _create_graph_base(my_name, include_me, input_txt_file, nx.DiGraph, followers_file_path=followers_file_path)


def create_undirected_graph_from_txt(my_name, include_me, input_txt_file, followers_file_path=None):
    return _create_graph_base(my_name, include_me, input_txt_file, nx.Graph, followers_file_path=followers_file_path)


CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')

def load_config():
    """
    Loads the configuration from ../config.json.
    Handles FileNotFoundError and json.JSONDecodeError.
    Returns the loaded config dictionary or None if an error occurs.
    """
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {CONFIG_FILE_PATH}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_FILE_PATH}")
        return None

def get_username_from_config(config=None):
    """
    Retrieves the username from the config.
    If config is not provided, it calls load_config().
    Handles KeyError if 'username' is not found.
    Returns the username or None if an error occurs.
    """
    if config is None:
        config = load_config()
    
    if config is not None:
        try:
            username = config['username']
            return username
        except KeyError:
            print("Error: 'username' not found in the configuration file.")
            return None
    return None


def add_cluster_to_json(input_dict, cluster_dict):
    nodes = input_dict['nodes']
    links = input_dict['links']

    for item in nodes:
        item['group'] = cluster_dict[item['name']]

    out_dict = {'nodes': nodes, 'links': links}

    return out_dict
