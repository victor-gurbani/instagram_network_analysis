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

    centrality_measures = [
        {'name': 'Betweenness Centrality', 'func': nx.betweenness_centrality},
        {'name': 'Closeness Centrality', 'func': nx.closeness_centrality},
        {'name': 'In-Degree Centrality', 'func': nx.in_degree_centrality},
        {'name': 'Out-Degree Centrality', 'func': nx.out_degree_centrality},
        {'name': 'PageRank', 'func': nx.pagerank}
    ]

    table_data_columns = []
    column_labels = []

    for measure_config in centrality_measures:
        name = measure_config['name']
        func = measure_config['func']
        
        print(f"\n # {name}:")
        
        # Calculate centrality
        centrality_values = func(G)
        
        # Get top 8 and bottom 8
        sorted_top = sort_and_small_dict(centrality_values, 8)
        sorted_bottom = reverse_sort_and_small_dict(centrality_values, 8)
        
        pprint.pprint(sorted_top)
        pprint.pprint(sorted_bottom)
        
        # Prepare data for table
        table_data_columns.append(centrality_to_str_arr(sorted_top) + centrality_to_str_arr(sorted_bottom))
        column_labels.append(name)

    # Table summarising results
    fig, ax = plt.subplots()
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')
    
    if table_data_columns: # Ensure there's data to plot
        data_for_table = np.transpose(table_data_columns)
        table = ax.table(colLabels=column_labels,
                         cellText=data_for_table,
                         loc='center')
        for (row, col), cell in table.get_celld().items():
            if (row == 0) or (col == -1): # Bold header row and index column
                cell.set_text_props(fontproperties=FontProperties(weight='bold'))
    else:
        print("No centrality data to display in table.")

    fig.tight_layout()
    plt.savefig("./centrality.png", dpi=300)
    plt.show()

if __name__ == '__main__':
    default_username = get_username_from_config()
    if default_username is None:
        print("Error: Username could not be loaded from config. Please check config.json.")
        # Potentially exit or set a fallback
        pass

    parser = argparse.ArgumentParser(description='Local analysis script')

    # Input parameters
    parser.add_argument('--username', type=str, default=default_username,
                        help='Username (default from config.json)')
    parser.add_argument('--input_txt_file', type=str, default='relations.txt',
                        help='Input text file (default: relations.txt)')
    parser.add_argument('--include_me', type=str2bool, nargs='?', const=True, default=False,
                        help='Include current user in analysis (default: False)')

    config = parser.parse_args()

    local_analysis(config)

