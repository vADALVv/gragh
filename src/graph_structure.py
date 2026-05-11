from __future__ import annotations

import random
from typing import Tuple, Dict
import networkx as nx
from dataclasses import dataclass


# =========================================================
# STATE MODEL (ALL NODES)
# =========================================================

@dataclass
class UserState:
    b: float
    c: float
    e: float


SEED = 42
random.seed(SEED)


def create_graph(
    num_u: int,
    num_r: int,
    num_l: int,
    avg_degree: int
) -> Tuple[nx.DiGraph, Dict[int, UserState], Dict[int, str]]:

    if num_u <= 0:
        raise ValueError("num_u must be > 0")

    # -------------------------
    # USER GRAPH
    # -------------------------
    k = max(2, int(avg_degree * 0.7))
    if k % 2 != 0:
        k += 1

    G_u = nx.newman_watts_strogatz_graph(
        n=num_u,
        k=min(k, num_u - 1),
        p=0.3,
        seed=SEED
    )

    G = G_u.to_directed()

    users: Dict[int, UserState] = {}
    roles: Dict[int, str] = {}

    # ALL nodes start as users
    for node in G.nodes():
        users[node] = UserState(
            b=random.uniform(-1, 1),
            c=random.uniform(0.3, 0.9),
            e=random.uniform(-1, 1)
        )
        roles[node] = "U"

    next_id = len(G.nodes())
    base_nodes = list(G.nodes())

    # -------------------------
    # RED AGENTS
    # -------------------------
    for _ in range(num_r):
        G.add_node(next_id)
        roles[next_id] = "R"

        users[next_id] = UserState(
            b=random.uniform(-1, 1),
            c=random.uniform(0.3, 0.9),
            e=random.uniform(-1, 1)
        )

        targets = random.sample(base_nodes, min(len(base_nodes), avg_degree * 2))
        for t in targets:
            G.add_edge(next_id, t, weight=random.uniform(0.5, 1.0))

        next_id += 1

    # -------------------------
    # LLM AGENTS
    # -------------------------
    for _ in range(num_l):
        G.add_node(next_id)
        roles[next_id] = "L"

        users[next_id] = UserState(
            b=random.uniform(-1, 1),
            c=random.uniform(0.3, 0.9),
            e=random.uniform(-1, 1)
        )

        targets = random.sample(base_nodes, min(len(base_nodes), avg_degree))
        for t in targets:
            G.add_edge(next_id, t, weight=random.uniform(0.5, 1.0))

        next_id += 1

    return G, users, roles