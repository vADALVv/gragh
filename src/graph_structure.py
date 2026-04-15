from __future__ import annotations

import random
from typing import Dict, Tuple

import networkx as nx

from threat_simulation import UserState


SEED = 42
random.seed(SEED)


def _validate_inputs(num_u, num_r, num_l, avg_degree):
    if num_u <= 0:
        raise ValueError("num_u must be > 0")
    if avg_degree <= 0:
        raise ValueError("avg_degree must be > 0")


def create_graph(
    num_u: int,
    num_r: int,
    num_l: int,
    avg_degree: int
) -> Tuple[nx.DiGraph, Dict[int, UserState], Dict[int, str]]:

    _validate_inputs(num_u, num_r, num_l, avg_degree)

    # -----------------------------
    # 1. U graph
    # -----------------------------
    num_groups = max(2, num_u // 50 or 1)
    sizes = [num_u // num_groups] * num_groups

    p_intra = min(0.3, avg_degree / max(num_u, 1))
    p_inter = p_intra * 0.1

    probs = [
        [p_intra if i == j else p_inter for j in range(num_groups)]
        for i in range(num_groups)
    ]

    G_u = nx.stochastic_block_model(sizes, probs, seed=SEED)
    G = G_u.to_directed()

    # -----------------------------
    # 2. Users (FIXED)
    # -----------------------------
    users: Dict[int, UserState] = {}
    roles: Dict[int, str] = {}

    for node in G.nodes():
        users[node] = UserState(
            b=random.uniform(-1, 1),
            c=random.uniform(0.3, 0.9),   # ✅ вместо s
            e=random.uniform(-1, 1)
        )
        roles[node] = "U"

    next_id = len(G.nodes())
    all_users = list(users.keys())

    # -----------------------------
    # 3. Red nodes
    # -----------------------------
    for _ in range(num_r):
        G.add_node(next_id)
        roles[next_id] = "R"

        targets = random.sample(all_users, min(len(all_users), avg_degree * 2))
        for t in targets:
            G.add_edge(next_id, t, weight=random.uniform(0.5, 1.0))

        next_id += 1

    # -----------------------------
    # 4. LLM nodes
    # -----------------------------
    for _ in range(num_l):
        G.add_node(next_id)
        roles[next_id] = "L"

        targets = random.sample(all_users, min(len(all_users), avg_degree))
        for t in targets:
            G.add_edge(next_id, t, weight=random.uniform(0.4, 0.9))

        next_id += 1

    return G, users, roles