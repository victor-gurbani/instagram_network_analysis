import json
import argparse

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def relations_to_json(config):
    username = config.username
    include_me = config.include_me
    input_txt_file = config.input_txt_file
    output_json_file = config.output_json_file

    if not username:
        with open('../config.json') as config_file:
            conf = json.load(config_file)
            username = conf['username']

    nodes = set()
    edges = set()
    data = {}
    name_to_id = {}

    with open(config.followers_file, 'r') as ffol:
        for line in ffol:
            follower = line.strip()
            if follower:
                nodes.add(follower)
                if include_me:
                    edges.add((follower, username)) # add an edge to you 
                    nodes.add(username)
        
    

    with open(input_txt_file, 'r') as f:
        for line in f:
            accounts = line.strip().split()
            if len(accounts) < 2:
                continue
            account_1 = accounts[0]
            account_2 = accounts[1]

            nodes.add(account_1)
            nodes.add(account_2)

            if include_me or (account_1 != username and account_2 != username):
                edges.add((account_1, account_2))

    if not include_me and username in nodes:
        nodes.remove(username)

    data["nodes"] = []
    id_n = 0
    for account in nodes:
        data["nodes"].append({"id": id_n, "name": account, "group": 1})
        name_to_id[account] = id_n
        id_n += 1

    data["links"] = []
    bi_links = set()
    id_l = 0
    for accounts in edges:
        id_1 = name_to_id[accounts[0]]
        id_2 = name_to_id[accounts[1]]
        if (accounts[1], accounts[0]) in edges:
            bi_links.add((id_1, id_2))
            if (id_2, id_1) not in bi_links:
                data["links"].append({
                    "id": id_l,
                    "source": id_1,
                    "target": id_2,
                    "value": 0.3,
                    "bi_directional": True
                })
                id_l += 1
        else:
            data["links"].append({
                "id": id_l,
                "source": id_1,
                "target": id_2,
                "value": 0.3,
                "bi_directional": False
            })
            id_l += 1

    with open(output_json_file, 'w') as outfile:
        json.dump(data, outfile)

    print("json created")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert relations to JSON format.')
    parser.add_argument('--username', type=str, default=None, help='Username to exclude from nodes (optional).')
    parser.add_argument('--input_txt_file', type=str, default='relations.txt', help='Input text file (default: relations.txt).')
    parser.add_argument('--output_json_file', type=str, default='relations.json', help='Output JSON file (default: relations.json).')
    parser.add_argument('--include_me', type=str2bool, nargs='?', const=True, default=False, help='Include username in nodes as directed edges follower -> username (default: False).')
    parser.add_argument('--followers_file', type=str, default='followers.txt', help='File containing your followers (default: followers.txt).')

    config = parser.parse_args()
    relations_to_json(config)

