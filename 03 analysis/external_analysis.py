import argparse
import json
import pprint
import matplotlib.pyplot as plt
import numpy as np
import os
import collections
from matplotlib.font_manager import FontProperties
from helper_functions import *


def external_analysis(config):
    my_name = config.username
    include_me = config.include_me
    input_txt_file = config.input_txt_file
    followers_data_dir = config.followers_data_dir
    followers_file = config.followers_file

    # Load the network graph first to know who is in the network
    # We use the graph to check for existing edges (for "Latent Friends")
    G_undirected = create_undirected_graph_from_txt(
        my_name, include_me, input_txt_file, followers_file_path=followers_file
    )
    network_members = set(G_undirected.nodes())

    print(f"Network: {len(network_members)} members loaded in graph.")

    # Load external followee data
    print(f"\nLoading external followee data from {followers_data_dir}...")
    followee_sets = load_external_followees(followers_data_dir, network_members)

    # Filter followee_sets to only include those in the network (if files exist for non-network members)
    # The prompt implies we analyze "network members"
    followee_sets = {k: v for k, v in followee_sets.items() if k in network_members}

    if not followee_sets:
        print(
            "Error: No followee data found for network members. Cannot proceed with external analysis."
        )
        return

    users_with_data = list(followee_sets.keys())
    print(f"Analysis will run on {len(users_with_data)} network members with data.")
    print("=" * 60)

    table_data_columns = []
    column_labels = []

    # --- 1. Hidden Homophily (Jaccard Similarity) ---
    print("\n### 1. Hidden Homophily (Jaccard Similarity of External Followees)")
    print("-" * 50)

    jaccard_scores = []
    latent_friends = []

    # Iterate over all unique pairs
    for i in range(len(users_with_data)):
        u1 = users_with_data[i]
        set1 = followee_sets[u1]
        for j in range(i + 1, len(users_with_data)):
            u2 = users_with_data[j]
            set2 = followee_sets[u2]

            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))

            if union > 0:
                score = intersection / union
                jaccard_scores.append(((u1, u2), score))

                # Check for latent friendship (high score, no edge)
                if score > config.jaccard_threshold:
                    if not G_undirected.has_edge(u1, u2):
                        latent_friends.append(((u1, u2), score))

    # Sort stats
    jaccard_scores.sort(key=lambda x: x[1], reverse=True)
    latent_friends.sort(key=lambda x: x[1], reverse=True)

    scores_only = [s for _, s in jaccard_scores]
    avg_jaccard = np.mean(scores_only) if scores_only else 0
    median_jaccard = np.median(scores_only) if scores_only else 0
    std_jaccard = np.std(scores_only) if scores_only else 0

    print(f"Analyzed {len(jaccard_scores)} pairs.")
    print(f"Average Jaccard Similarity: {avg_jaccard:.4f}")
    print(f"Median: {median_jaccard:.4f}, Std Dev: {std_jaccard:.4f}")

    print("\nTop 20 pairs by Jaccard similarity:")
    top_pairs_str = []
    for (u1, u2), score in jaccard_scores[:20]:
        print(f"  {u1} <--> {u2}: {score:.4f}")
        if len(top_pairs_str) < 16:
            top_pairs_str.append(f"{u1}<->{u2} | {score:.2f}")

    print(
        f"\nTop 20 Latent Friends (Jaccard > {config.jaccard_threshold}, no direct link):"
    )
    for (u1, u2), score in latent_friends[:20]:
        print(f"  {u1} <--> {u2}: {score:.4f}")

    # Add to table data
    # Padding if less than 16
    while len(top_pairs_str) < 16:
        top_pairs_str.append("")

    # Split into two columns for the table (top 8 and next 8)
    # But user asked for "Top Jaccard Pairs" as one column group in description
    # "Top 16 pairs formatted as 'user1<->user2 | 0.35'"
    # In advanced_analysis, it adds top 8 and bottom 8. Here we just add top 16.
    table_data_columns.append(top_pairs_str)
    column_labels.append("Top Jaccard Pairs")

    # --- 2. Shadow Centers (Passive Cultural Hubs) ---
    print("\n\n### 2. Shadow Centers (Passive Cultural Hubs)")
    print("-" * 50)

    external_counts = collections.defaultdict(int)
    for user, followees in followee_sets.items():
        for followee in followees:
            # Filter out accounts that are already in the network or is the user themselves
            if followee not in network_members and followee != my_name:
                external_counts[followee] += 1

    # Convert to list for sorting

    shadow_centers = []
    total_network_size = len(network_members)  # or len(users_with_data)?
    # "percentage of network" implies size of network graph or size of analyzed users.
    # We'll use len(users_with_data) as the denominator for percentage
    denominator = len(users_with_data)

    for acc, count in external_counts.items():
        shadow_centers.append(
            {
                "name": acc,
                "follower_count": count,
                "percentage": (count / denominator) * 100,
            }
        )

    shadow_centers.sort(key=lambda x: x["follower_count"], reverse=True)

    print(
        f"Found {len(external_counts)} unique external accounts followed by network members."
    )
    print(f"\nTop {config.top_k_shadow} Shadow Centers:")

    for i, item in enumerate(shadow_centers[: config.top_k_shadow]):
        cat = ""
        if item["percentage"] > 75:
            cat = "(Universal Hub)"
        elif item["percentage"] > 50:
            cat = "(Major Hub)"
        elif item["percentage"] > 25:
            cat = "(Minor Hub)"

        print(
            f"  {i + 1}. {item['name']}: {item['follower_count']} followers ({item['percentage']:.1f}%) {cat}"
        )

    # --- 3. 2nd Degree Reach (Structural Hole Value) ---
    print("\n\n### 3. 2nd Degree Reach (Structural Hole Value)")
    print("-" * 50)

    # Pre-calculate global counts to speed up unique check
    # An external account is "unique" to user U if count[acc] == 1 and acc in followees[U]
    # But we need to be careful: unique means unique *among network members*
    # We already have external_counts which counts how many network members follow each external account.
    # So if external_counts[acc] == 1, it is followed by exactly one network member.

    reach_stats = []

    for user in users_with_data:
        followees = followee_sets[user]

        # External accounts this user follows
        my_external = [f for f in followees if f not in network_members]
        total_external = len(my_external)

        # Unique external: count how many have count == 1 in external_counts
        unique_external = sum(1 for f in my_external if external_counts[f] == 1)

        unique_ratio = unique_external / max(total_external, 1)

        reach_stats.append((user, total_external, unique_external, unique_ratio))

    # Sort and display
    # Top 20 by unique_external
    print("\nTop 20 by Unique Reach (accounts only they follow):")
    reach_stats.sort(key=lambda x: x[2], reverse=True)
    top_unique = reach_stats[:20]
    for r in top_unique:
        print(f"  {r[0]}: {r[2]} unique accounts")

    # Top 20 by unique_ratio
    print("\nTop 20 by Unique Ratio (most distinctive taste):")
    reach_stats.sort(key=lambda x: x[3], reverse=True)
    top_ratio = reach_stats[:20]
    for r in top_ratio:
        print(f"  {r[0]}: {r[3]:.4f} ratio ({r[2]}/{r[1]})")

    # Top 20 by total_external
    print("\nTop 20 by Total External Reach:")
    reach_stats.sort(key=lambda x: x[1], reverse=True)
    top_total = reach_stats[:20]
    for r in top_total:
        print(f"  {r[0]}: {r[1]} accounts")

    # Bottom 10 by unique_ratio
    print("\nBottom 10 by Unique Ratio (most mainstream):")
    reach_stats.sort(key=lambda x: x[3])
    bottom_ratio = reach_stats[:10]
    for r in bottom_ratio:
        print(f"  {r[0]}: {r[3]:.4f}")

    # Add to table data: "Unique Reach" (top 8 + bottom 8)
    # We'll use the unique_external count for the table
    reach_stats.sort(key=lambda x: x[2], reverse=True)  # Sort by unique count again
    top_8_unique = [(r[0], r[2]) for r in reach_stats[:8]]
    bottom_8_unique = [(r[0], r[2]) for r in reach_stats[-8:]]

    # We need to reverse the bottom ones so the smallest is at the bottom of the list visually?
    # advanced_analysis uses reverse_sort_and_small_dict which returns smallest first?
    # Actually helper function `reverse_sort_and_small_dict` returns smallest values.
    # In advanced_analysis: `bottom_clustered = reverse_sort_and_small_dict(...)`
    # then `centrality_to_str_arr(sorted_top) + centrality_to_str_arr(sorted_bottom)`
    # This implies the column has high values at top, low values at bottom.

    # Let's get bottom 8 with lowest unique counts (likely 0)
    # reach_stats is sorted desc by unique count.
    bottom_8_unique = [(r[0], r[2]) for r in reach_stats[-8:]]

    table_data_columns.append(
        centrality_to_str_arr(top_8_unique) + centrality_to_str_arr(bottom_8_unique)
    )
    column_labels.append("Unique Reach")

    # --- 4. Echo Chamber Score ---
    print("\n\n### 4. Echo Chamber Score")
    print("-" * 50)

    # popular_followees = accounts followed by > 25% of network members
    threshold_count = 0.25 * len(users_with_data)
    popular_followees = set(
        acc for acc, count in external_counts.items() if count > threshold_count
    )

    print(
        f"Defined {len(popular_followees)} popular external accounts (>25% coverage)."
    )

    conformity_stats = []

    for user in users_with_data:
        followees = followee_sets[user]
        if not popular_followees:
            score = 0
        else:
            intersection = len(followees.intersection(popular_followees))
            score = intersection / len(popular_followees)
        conformity_stats.append((user, score, len(followees)))

    conformity_stats.sort(key=lambda x: x[1], reverse=True)

    print("\nTop 10 Echo Chamber Users (highest conformity):")
    for r in conformity_stats[:10]:
        print(f"  {r[0]}: {r[1]:.4f}")

    # Mavericks: lowest conformity among users with > 100 followees
    mavericks = [r for r in conformity_stats if r[2] > 100]
    mavericks.sort(key=lambda x: x[1])

    print("\nTop 10 Mavericks (lowest conformity, >100 followees):")
    for r in mavericks[:10]:
        print(f"  {r[0]}: {r[1]:.4f}")

    avg_conformity = (
        np.mean([r[1] for r in conformity_stats]) if conformity_stats else 0
    )
    print(f"\nNetwork-wide conformity average: {avg_conformity:.4f}")

    # Add to table data: "Echo Chamber" (top 8 + bottom 8)
    top_8_echo = [(r[0], r[1]) for r in conformity_stats[:8]]
    bottom_8_echo = [(r[0], r[1]) for r in conformity_stats[-8:]]

    table_data_columns.append(
        centrality_to_str_arr(top_8_echo) + centrality_to_str_arr(bottom_8_echo)
    )
    column_labels.append("Echo Chamber")

    # --- 5. Interest Bridges (Cross-Community Latent Links) ---
    print("\n\n### 5. Interest Bridges (Cross-Community Latent Links)")
    print("-" * 50)

    louvain_path = config.louvain_json
    # Check if we should look in current dir or root? Config default is filename only.
    # Try current dir
    if not os.path.exists(louvain_path):
        # Try one level up if not found? No, follow strict path
        pass

    community_map = {}
    if os.path.exists(louvain_path):
        try:
            with open(louvain_path, "r") as f:
                l_data = json.load(f)
            for node in l_data.get("nodes", []):
                if "name" in node:
                    community_map[node["name"]] = node.get("group", 0)

            print(f"Loaded community data for {len(community_map)} nodes.")

            bridges = []
            # Use ALL high-Jaccard pairs (not just latent_friends) to find
            # cross-community interest overlap — including connected pairs
            for (u1, u2), score in jaccard_scores:
                if score < config.jaccard_threshold:
                    break  # jaccard_scores is sorted desc, so stop early

                if u1 in community_map and u2 in community_map:
                    if community_map[u1] != community_map[u2]:
                        has_edge = G_undirected.has_edge(u1, u2)
                        bridges.append(
                            (
                                (u1, u2),
                                score,
                                community_map[u1],
                                community_map[u2],
                                has_edge,
                            )
                        )

            bridges.sort(key=lambda x: x[1], reverse=True)

            print(f"\nTop 15 Interest Bridges (High Jaccard, Different Communities):")
            for item in bridges[:15]:
                (u1, u2), score, c1, c2, has_edge = item
                link = "linked" if has_edge else "unlinked"
                print(f"  {u1} (Comm {c1}) <--> {u2} (Comm {c2}): {score:.4f} [{link}]")

        except Exception as e:
            print(f"Error reading community data: {e}")
    else:
        print(
            "Community data not found (relations_louvain.json). Run community_detection.py first for Interest Bridge analysis."
        )

    # --- Export JSON ---
    print(f"\n\n### Exporting Analysis to {config.output_json}")
    print("-" * 50)

    try:
        # Load original relations.json to preserve structure
        with open(config.input_json_file, "r") as f:
            export_data = json.load(f)

        # Create lookups for stats
        # reach_stats: (user, total, unique, ratio)
        reach_map = {
            r[0]: {"total": r[1], "unique": r[2], "ratio": r[3]} for r in reach_stats
        }

        # conformity_stats: (user, score, len)
        echo_map = {r[0]: r[1] for r in conformity_stats}

        # Latent friends: top 1 per user?
        # Let's find top latent friend for each user
        top_latent_map = {}
        for (u1, u2), score in latent_friends:
            if u1 not in top_latent_map or score > top_latent_map[u1][1]:
                top_latent_map[u1] = (u2, score)
            if u2 not in top_latent_map or score > top_latent_map[u2][1]:
                top_latent_map[u2] = (u1, score)

        # Update nodes
        for node in export_data["nodes"]:
            name = node.get("name")
            if name in reach_map:
                node["unique_reach"] = reach_map[name]["unique"]
                node["total_external_reach"] = reach_map[name]["total"]
                node["unique_ratio"] = float(f"{reach_map[name]['ratio']:.4f}")

            if name in echo_map:
                node["echo_chamber_score"] = float(f"{echo_map[name]:.4f}")

            if name in top_latent_map:
                node["top_latent_friend"] = top_latent_map[name][0]
                node["top_latent_jaccard"] = float(f"{top_latent_map[name][1]:.4f}")

        # Add global stats
        export_data["shadow_centers"] = shadow_centers[:50]

        # Latent friendships list
        latent_list = []
        for (u1, u2), score in latent_friends[:100]:  # Limit to top 100 to avoid bloat
            latent_list.append(
                {
                    "user1": u1,
                    "user2": u2,
                    "jaccard": float(f"{score:.4f}"),
                    "connected": False,
                }
            )
        export_data["latent_friendships"] = latent_list

        with open(config.output_json, "w") as f:
            json.dump(export_data, f, indent=4)
        print(f"Data exported successfully to {config.output_json}")

    except Exception as e:
        print(f"Error exporting JSON: {e}")

    # --- Generate Image ---
    print("\nGenerating results table image...")
    fig, ax = plt.subplots(figsize=(12, 8) if len(column_labels) > 2 else (8, 6))
    fig.patch.set_visible(False)
    ax.axis("off")
    ax.axis("tight")

    if table_data_columns:
        # Pad columns to same length if needed (though we tried to ensure 16 rows)
        max_len = max(len(col) for col in table_data_columns)
        padded_columns = []
        for col in table_data_columns:
            new_col = col + [""] * (max_len - len(col))
            padded_columns.append(new_col)

        data_for_table = np.transpose(padded_columns)
        table = ax.table(colLabels=column_labels, cellText=data_for_table, loc="center")

        # Styling
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.2)

        for (row, col), cell in table.get_celld().items():
            if (row == 0) or (col == -1):
                cell.set_text_props(fontproperties=FontProperties(weight="bold"))

        output_image_path = "./external_analysis_results.png"
        fig.tight_layout()
        plt.savefig(output_image_path, dpi=300, bbox_inches="tight")
        print(f"Results image saved to {output_image_path}")
    else:
        print("No data to display in table.")

    print("\n" + "=" * 60)
    print("External analysis complete.")


if __name__ == "__main__":
    # Load default username from config
    default_username = get_username_from_config()

    parser = argparse.ArgumentParser(
        description="Dark Matter network analysis on full followee lists"
    )

    parser.add_argument("--username", type=str, default=default_username)
    parser.add_argument("--input_txt_file", type=str, default="relations.txt")
    parser.add_argument("--input_json_file", type=str, default="relations.json")
    parser.add_argument(
        "--include_me", type=str2bool, nargs="?", const=True, default=False
    )
    parser.add_argument("--followers_file", type=str, default="followers.txt")
    parser.add_argument(
        "--followers_data_dir", type=str, default="../01 scraping/followers_data/"
    )
    parser.add_argument("--louvain_json", type=str, default="relations_louvain.json")
    parser.add_argument("--output_json", type=str, default="relations_darkmatter.json")
    parser.add_argument("--top_k_shadow", type=int, default=50)
    parser.add_argument("--jaccard_threshold", type=float, default=0.15)

    config = parser.parse_args()

    external_analysis(config)
