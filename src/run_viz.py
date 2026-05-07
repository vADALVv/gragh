#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from networkx import DiGraph

from visualization import visualize_graph


# =====================================================
# CONFIG
# =====================================================

RESULTS_FILE = "simulation_result.json"


# =====================================================
# LOAD
# =====================================================

def load_results(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================
# GRAPH BUILD
# =====================================================

def build_graph(timeline):
    G = DiGraph()

    for event in timeline:
        src = event.get("from")
        dst = event.get("to")

        if src is None or dst is None:
            continue

        G.add_edge(src, dst)

    return G


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    print("[INFO] Loading simulation_result.json...")

    results = load_results(RESULTS_FILE)

    print("[OK] Loaded")

    timeline = results.get("timeline", [])

    users = results.get("users_initial", {})
    node_types = results.get("node_types", {})

    if not timeline:
        raise ValueError("Timeline is empty. Nothing to visualize.")

    print("[INFO] Building graph...")

    G = build_graph(timeline)

    print("[INFO] Launching visualization...")

    visualize_graph(
        G=G,
        results=results,
        users=users,
        node_types=node_types,
        blue_agent=None
    )

    print("[DONE] Visualization complete")