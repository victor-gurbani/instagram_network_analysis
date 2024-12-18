import argparse
import json
from helper_functions import *
import pprint
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties

def local_analysis(config):
    my_name = config.username
    include_me = config.include_me
    input_txt_file = config.input_txt_file

    G = create_graph_from_txt(my_name, include_me, input_txt_file)

    # Betweenness centrality
    bet_cen = nx.betweenness_centrality(G)
    bet_cen = sort_and_small_dict(bet_cen, 8)
    bet_cenR = sort_and_small_dict(bet_cen, 8)
    
    # Closeness centrality
    clo_cen = nx.closeness_centrality(G)
    clo_cen = sort_and_small_dict(clo_cen, 8)
    clo_cenR = sort_and_small_dict(clo_cen, 8)
    
    # In-Degree centrality
    in_deg_cen = nx.in_degree_centrality(G)
    in_deg_cen = sort_and_small_dict(in_deg_cen, 8)
    in_deg_cenR = sort_and_small_dict(in_deg_cen, 8)
    
    # Out-Degree centrality
    out_deg_cen = nx.out_degree_centrality(G)
    out_deg_cen = sort_and_small_dict(out_deg_cen, 8)
    out_deg_cenR = sort_and_small_dict(out_deg_cen, 8)
    
    # PageRank
    page_rank = nx.pagerank(G)
    page_rank = sort_and_small_dict(page_rank, 8)
    page_rankR = sort_and_small_dict(page_rank, 8)

    # Print centralities
    print("\n # Betweenness centrality:")
    pprint.pprint(bet_cen)
    pprint.pprint(bet_cenR)
    print("\n # Closeness centrality:")
    pprint.pprint(clo_cen)
    pprint.pprint(clo_cenR)
    print("\n # In-Degree centrality:")
    pprint.pprint(in_deg_cen)
    pprint.pprint(in_deg_cenR)
    print("\n # Out-Degree centrality:")
    pprint.pprint(out_deg_cen)
    pprint.pprint(out_deg_cenR)
    print("\n # Page rank:")
    pprint.pprint(page_rank)
    pprint.pprint(page_rankR)

    # Table summarising results
    fig, ax = plt.subplots()
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')
    data = [centrality_to_str_arr(bet_cen)+centrality_to_str_arr(bet_cenR),
            centrality_to_str_arr(clo_cen)+centrality_to_str_arr(clo_cenR),
            centrality_to_str_arr(in_deg_cen)+centrality_to_str_arr(in_deg_cenR),
            centrality_to_str_arr(out_deg_cen)+centrality_to_str_arr(out_deg_cenR),
            centrality_to_str_arr(page_rank)+centrality_to_str_arr(page_rankR)]
    data = np.transpose(data)
    table = ax.table(colLabels=['Betweenness Centrality', 'Closeness Centrality', 'In-Degree Centrality', 'Out-Degree Centrality', 'PageRank'],
                     cellText=data,
                     loc='center')
    for (row, col), cell in table.get_celld().items():
        if (row == 0) or (col == -1):
            cell.set_text_props(fontproperties=FontProperties(weight='bold'))
    fig.tight_layout()
    plt.savefig("./centrality.png", dpi=300)
    plt.show()

if __name__ == '__main__':
    # Read default username from '../config.json'
    with open('../config.json') as config_file:
        conf = json.load(config_file)
    default_username = conf['username']

    parser = argparse.ArgumentParser(description='Local analysis script')

    # Input parameters
    parser.add_argument('--username', type=str, default=default_username,
                        help='Username (default: value from ../config.json)')
    parser.add_argument('--input_txt_file', type=str, default='relations.txt',
                        help='Input text file (default: relations.txt)')
    parser.add_argument('--include_me', type=str2bool, nargs='?', const=True, default=False,
                        help='Include current user in analysis (default: False)')

    config = parser.parse_args()

    local_analysis(config)

