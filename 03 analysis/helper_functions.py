import re
import networkx as nx
import argparse
import collections
import scipy.optimize
import json  # Added for config loading
import os  # Added for path manipulation for config loading


def fit_powerlaw(degrees, counts):
    if min(degrees) == 0:
        x = degrees[:-1]
        y = counts[:-1]
    else:
        x = degrees
        y = counts

    def powerlaw(x, a, b):
        return a * (x**b)

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
        str_arr.append(item[0] + " | " + str(round(item[1], 2)))
    return str_arr


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def _create_graph_base(
    my_name, include_me, input_txt_file, graph_type, followers_file_path=None
):
    nodes = set()  # This will be our nodes_set
    edges = []
    G = graph_type()

    # Add nodes from followers_file_path first, if provided
    if followers_file_path:
        try:
            with open(followers_file_path, "r") as f_followers:
                for line in f_followers:
                    follower_username = line.strip()
                    if follower_username:  # Ensure not an empty line
                        nodes.add(follower_username)
            print(
                f"Successfully loaded {len(nodes)} initial nodes from {followers_file_path}"
            )
        except FileNotFoundError:
            print(
                f"Warning: Followers file {followers_file_path} not found. Proceeding without it."
            )
        except Exception as e:
            print(
                f"Warning: Error reading {followers_file_path}: {e}. Proceeding without it."
            )

    # Add nodes and edges from the main input_txt_file
    try:
        with open(input_txt_file, "r") as f:
            for line in f:
                accounts = line.split(" ")
                if len(accounts) < 2:
                    continue
                account_1 = accounts[0].strip()
                account_2 = accounts[1].strip()

                nodes.add(account_1)  # Add account_1 to nodes
                nodes.add(
                    account_2
                )  # Add account_2 to nodes, ensure both are added before filtering

                if include_me:
                    edges.append([account_1, account_2])
                else:
                    if not (account_1 == my_name or account_2 == my_name):
                        edges.append([account_1, account_2])
    except FileNotFoundError:
        print(f"Error: Main input file {input_txt_file} not found. Cannot build graph.")
        return G  # Return empty graph
    except Exception as e:
        print(
            f"Error: Could not read main input file {input_txt_file}: {e}. Cannot build graph."
        )
        return G  # Return empty graph

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
            if (
                acc_1 in G and acc_2 in G
            ):  # Ensure nodes exist in graph before adding edge
                G.add_edge(acc_1, acc_2)
    return G


def create_graph_from_txt(
    my_name, include_me, input_txt_file, followers_file_path=None
):  # Added followers_file_path to signature
    return _create_graph_base(
        my_name,
        include_me,
        input_txt_file,
        nx.DiGraph,
        followers_file_path=followers_file_path,
    )


def create_undirected_graph_from_txt(
    my_name, include_me, input_txt_file, followers_file_path=None
):
    return _create_graph_base(
        my_name,
        include_me,
        input_txt_file,
        nx.Graph,
        followers_file_path=followers_file_path,
    )


CONFIG_ENV_VAR = "INSTAGRAM_NETWORK_CONFIG"
CONFIG_FILE_PATH = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "..", "config.json")
)


def resolve_config_file_path(config_file_path=None):
    """Return the config path without depending on the process working directory.

    An explicit path takes precedence over ``INSTAGRAM_NETWORK_CONFIG``. If neither
    is set, the repository-root ``config.json`` is used. Relative overrides remain
    relative to the caller's working directory because they are intentional user
    input, while the default is anchored to this source file.
    """
    configured_path = config_file_path
    if configured_path is None:
        configured_path = os.environ.get(CONFIG_ENV_VAR) or CONFIG_FILE_PATH

    resolved_path = os.path.expanduser(os.fspath(configured_path))
    if not os.path.isabs(resolved_path):
        resolved_path = os.path.join(os.getcwd(), resolved_path)
    return os.path.abspath(resolved_path)


def load_config(config_file_path=None):
    """Load a JSON-object configuration, returning ``None`` on a clear error."""
    resolved_path = resolve_config_file_path(config_file_path)
    try:
        with open(resolved_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {resolved_path}")
        return None
    except json.JSONDecodeError as error:
        print(
            "Error: Could not decode JSON from "
            f"{resolved_path} (line {error.lineno}, column {error.colno})"
        )
        return None
    except UnicodeDecodeError as error:
        print(f"Error: Configuration file at {resolved_path} is not valid UTF-8: {error}")
        return None
    except OSError as error:
        print(f"Error: Could not read configuration file at {resolved_path}: {error}")
        return None

    if not isinstance(config, dict):
        print(f"Error: Configuration in {resolved_path} must be a JSON object.")
        return None
    return config


def get_username_from_config(config=None, config_file_path=None):
    """Return a nonblank username from a config mapping, if available."""
    if config is None:
        config = load_config(config_file_path)
    if config is None:
        return None
    if not isinstance(config, dict):
        print("Error: Configuration must be a mapping containing 'username'.")
        return None

    username = config.get("username")
    if not isinstance(username, str) or not username.strip():
        print("Error: 'username' must be a non-empty string in the configuration file.")
        return None
    return username.strip()


def resolve_username(username=None, config=None, config_file_path=None):
    """Prefer a supplied username, falling back to the configured username."""
    if username is not None:
        if isinstance(username, str) and username.strip():
            return username.strip()
        print("Error: The supplied username must be a non-empty string.")
        return None
    return get_username_from_config(config, config_file_path)


def add_cluster_to_json(input_dict, cluster_dict):
    nodes = input_dict["nodes"]
    links = input_dict["links"]

    for item in nodes:
        item["group"] = cluster_dict[item["name"]]

    out_dict = {"nodes": nodes, "links": links}

    return out_dict


def load_external_followees(followers_data_dir, network_usernames=None):
    """
    Load full followee sets from followers_data/ directory.

    Each file is named {username}.{userid}.txt and contains one followee username per line.

    Args:
        followers_data_dir: Path to the followers_data/ directory
        network_usernames: Optional set of usernames in the network (from followers.txt)

    Returns:
        dict: {username: set(followee_usernames)} for each file found
    """
    followee_sets = {}
    if not os.path.isdir(followers_data_dir):
        print(f"Warning: followers_data directory not found at {followers_data_dir}")
        return followee_sets

    for filename in os.listdir(followers_data_dir):
        if not filename.endswith(".txt"):
            continue
        # Extract username from filename format: username.userid.txt
        parts = filename.rsplit(".", 2)
        if len(parts) < 3:
            continue
        username = parts[0]

        filepath = os.path.join(followers_data_dir, filename)
        try:
            with open(filepath, "r") as f:
                followees = set(line.strip() for line in f if line.strip())
            followee_sets[username] = followees
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}")

    print(
        f"Loaded followee data for {len(followee_sets)} users "
        f"(avg {sum(len(v) for v in followee_sets.values()) / max(len(followee_sets), 1):.0f} followees each)"
    )
    return followee_sets
