import json
import numpy as np
import matplotlib.pyplot as plt
from gtda.homology import RipsPersistence
from gtda.diagrams import PersistenceDiagram
from gtda.plotting import plot_diagram

# Function to load and parse data
def load_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

# Function to extract player positions
def extract_positions(data):
    positions = []
    for player in data:
        x, y = player['x'], player['y']
        positions.append([x, y])  # Store player positions as [x, y]
    return np.array(positions)

# Create a Rips Complex and compute its persistence diagram
def compute_persistence_diagram(positions, threshold=10.0):
    # Initialize the RipsPersistence object
    rips_persistence = RipsPersistence(homology_dimensions=[0, 1, 2], persistence_threshold=threshold)
    
    # Fit the RipsComplex and compute persistence diagrams
    diagrams = rips_persistence.fit_transform([positions])  # Giotto requires the data in list format
    
    return diagrams[0]  # Return the persistence diagram for the first match

# Function to plot persistence diagram
def plot_persistence_diagram(diagram, title="Persistence Diagram"):
    plot_diagram(diagram)
    plt.title(title)
    plt.show()

# Function to plot player positions
def plot_field(positions, title="Player Positions"):
    plt.scatter(positions[:, 0], positions[:, 1], color='blue', label='Players')
    plt.title(title)
    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.show()

# Example: Load one of the datasets and process it
file_path = '/mnt/data/3890259_Bayern-Munich_2_55.json'  # Replace with the desired file
data = load_data(file_path)

# Extract player positions
positions = extract_pos
