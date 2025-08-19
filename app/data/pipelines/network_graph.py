# app/data/pipelines/network_graph.py

import json
import networkx as nx
import matplotlib.pyplot as plt

def build_network_graph():
    """Build a bipartite graph of Reps <-> Stocks."""
    with open("data/outputs/capitol_trades.json") as f:
        trades = json.load(f)

    G = nx.Graph()
    for trade in trades:
        rep = trade["rep"]
        ticker = trade["ticker"]
        G.add_edge(rep, ticker)

    # Find clusters
    communities = nx.community.greedy_modularity_communities(G)
    for i, comm in enumerate(communities):
        if len(comm) > 2:
            print(f"🔥 Cluster {i+1}: {comm}")

    # Save graph
    nx.write_gexf(G, "trading_logs/congress_network.gexf")
    return G
