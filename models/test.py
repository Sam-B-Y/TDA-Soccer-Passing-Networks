import json
import os
from typing import List, Dict
import numpy as np
import networkx as nx
from gtda.homology import FlagserPersistence
from gtda.diagrams import BettiCurve
import matplotlib.pyplot as plt
from gtda.plotting import plot_diagram

def load_game_data(file_path: str) -> List[Dict]:
    with open(file_path, 'r') as file:
        game_data = json.load(file)
    return game_data

def construct_adjacency_matrix(game: List[Dict]) -> nx.Graph:
    G = nx.Graph()

    counts = [pass_info["count"] for player in game for pass_info in player["passes"]]
    max_count = max(counts)
    min_count = min(counts)

    for player in game:
        G.add_node(player['name'], pos=(player['x'], player['y']))

    for player in game:
        for pass_info in player["passes"]:
            player1 = player["name"]
            player2 = pass_info["name"]
            count = pass_info["count"]

            # Normalize counts to [0, 1] and invert so that higher counts correspond to lower weights
            edge_weight = 1 - (count - min_count) / (max_count - min_count)

            G.add_edge(player1, player2, weight=edge_weight)

    return G

def visualize_passing_network(G):
    pos = nx.get_node_attributes(G, 'pos')
    weights = nx.get_edge_attributes(G, 'weight').values()
    
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue')
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    nx.draw_networkx_edges(G, pos, width=2, edge_color='gray')
    plt.title("Passing Network Graph")
    plt.axis('off')
    plt.show()

# Load the game data
example_game = load_game_data('../data/2015-2016/1-Bundesliga/3890260_Bayer-Leverkusen_1_59.json')

# Construct the graph
G_example = construct_adjacency_matrix(example_game)
visualize_passing_network(G_example)

# Compute persistent homology
from gtda.homology import FlagserPersistence
fp = FlagserPersistence()
diagrams = fp.fit_transform([G_example])[0]

# Plot persistence diagrams
from gtda.plotting import plot_diagram
plot_diagram(diagrams)

# Compute Betti curves
from gtda.diagrams import BettiCurve
betti_transformer = BettiCurve(n_bins=100)
betti_numbers = betti_transformer.fit_transform([diagrams])[0]

# Extract filtration values
filtration_values = np.linspace(diagrams[1: ,].min(), diagrams[1: ,].max(), num=100)

# Determine the maximum homology dimension
homology_dimensions = int(diagrams[:, 0].max()) + 1
betti_numbers = betti_numbers.reshape(-1, homology_dimensions)

# Extract Betti numbers for each dimension
betti0 = betti_numbers[:, 0]
betti1 = betti_numbers[:, 1] if homology_dimensions > 1 else None

# Plot Betti curves
plt.figure(figsize=(10, 6))
plt.plot(filtration_values, betti0, label=r'$\beta_0$ (Connected Components)', color='blue')
if betti1 is not None:
    plt.plot(filtration_values, betti1, label=r'$\beta_1$ (Cycles)', color='red')
plt.xlabel('Filtration Parameter')
plt.ylabel('Betti Numbers')
plt.title('Betti Curves Across Filtration')
plt.legend()
plt.grid(True)
plt.show()

# Print Betti numbers
print("Betti 0 (Connected Components) at various filtration levels:")
print(betti0)

if betti1 is not None:
    print("\nBetti 1 (Cycles) at various filtration levels:")
    print(betti1)
