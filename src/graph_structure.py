#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import random
from typing import Tuple, Dict

import networkx as nx


# ============================================================
# DATA MODEL
# ============================================================

class UserState:
    """Состояние обычного пользователя (U)."""
    def __init__(self, b: float, c: float, e: float):
        self.b = b   # bias
        self.c = c   # consistency
        self.e = e   # emotional factor

    def __repr__(self):
        return f"UserState(b={self.b:.3f}, c={self.c:.3f}, e={self.e:.3f})"


# ============================================================
# GLOBAL
# ============================================================

SEED = 42
random.seed(SEED)


# ============================================================
# VALIDATION
# ============================================================

def _validate_inputs(num_u: int, num_r: int, num_l: int, avg_degree: int) -> None:
    if num_u <= 0:
        raise ValueError("num_u must be > 0")
    if avg_degree <= 0:
        raise ValueError("avg_degree must be > 0")
    if num_r < 0 or num_l < 0:
        raise ValueError("num_r, num_l must be >= 0")


# ============================================================
# GRAPH CREATION
# ============================================================

def create_graph(
    num_u: int,
    num_r: int,
    num_l: int,
    avg_degree: int
) -> Tuple[nx.DiGraph, Dict[int, UserState], Dict[int, str]]:
    """
    Создаёт ориентированный граф с узлами:
        U – обычные пользователи (small-world)
        R – атакующие (red)
        L – LLM-узлы

    Возвращает:
        G         : граф (networkx.DiGraph)
        users     : состояния пользователей
        roles     : роли узлов
    """

    _validate_inputs(num_u, num_r, num_l, avg_degree)

    # ======== 1. Small-world граф пользователей ========
    k = max(2, int(avg_degree * 0.7))
    if k % 2 != 0:
        k += 1
    if k >= num_u:
        k = num_u - 1 if num_u % 2 == 0 else num_u - 2
        if k < 2:
            k = 2

    p = (avg_degree / k) - 1.0
    p = max(0.0, min(1.0, p))

    G_u = nx.newman_watts_strogatz_graph(
        n=num_u,
        k=k,
        p=p,
        seed=SEED
    )

    G = G_u.to_directed()

    # ======== 2. Инициализация пользователей ========
    users: Dict[int, UserState] = {}
    roles: Dict[int, str] = {}

    for node in G.nodes():
        users[node] = UserState(
            b=random.uniform(-1, 1),
            c=random.uniform(0.3, 0.9),
            e=random.uniform(-1, 1)
        )
        roles[node] = "U"

    next_id = len(G.nodes())
    all_users = list(users.keys())

    # ======== 3. Красные узлы (R) ========
    for _ in range(num_r):
        G.add_node(next_id)
        roles[next_id] = "R"

        targets = random.sample(all_users, min(len(all_users), avg_degree * 2))
        for t in targets:
            G.add_edge(next_id, t, weight=random.uniform(0.5, 1.0))

        next_id += 1

    # ======== 4. LLM-узлы (L) ========
    for _ in range(num_l):
        G.add_node(next_id)
        roles[next_id] = "L"

        targets = random.sample(all_users, min(len(all_users), avg_degree))
        for t in targets:
            G.add_edge(next_id, t, weight=random.uniform(0.5, 1.0))

        next_id += 1

    return G, users, roles