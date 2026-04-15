import json
import os
from graph_structure import create_graph
from simulation import simulate_diffusion
from visualization import visualize_graph

from threat_simulation import init_message_bank

init_message_bank(r"C:\Users\Vlada\Desktop\llm_attaks\graph\data\messages.txt")
# =====================================================
# CONFIG
# =====================================================

N_USERS = 15
N_RED = 2
N_LLM = 1
AVG_DEGREE = 4
T_STEPS = 30

OUTPUT_FILE = "simulation_results.json"


# =====================================================
# GRAPH
# =====================================================

G, users, node_types = create_graph(
    num_u=N_USERS,
    num_r=N_RED,
    num_l=N_LLM,
    avg_degree=AVG_DEGREE
)


# =====================================================
# SIMULATION
# =====================================================

results = simulate_diffusion(
    G=G,
    users=users,
    node_types=node_types,
    T_steps=T_STEPS,
    seed=42
)


# =====================================================
# SAVE RESULTS
# =====================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"[OK] saved → {OUTPUT_FILE}")


if not os.path.exists(OUTPUT_FILE):
    raise RuntimeError("Simulation output not created")


# =====================================================
# BLUE AGENT (REAL IMPORT)
# =====================================================

print("[INFO] loading Blue Agent...")

try:
    from blue_agent import BlueAgent

    # пока без LLM модели → используется rule-based версия внутри blue_agent.py
    blue_agent = BlueAgent()

    print("[OK] Blue Agent loaded")

except Exception as e:
    print(f"[ERROR] Blue Agent import failed: {e}")
    blue_agent = None


# =====================================================
# VISUALIZATION
# =====================================================

print("[INFO] launching visualization...")

visualize_graph(
    G=G,
    results=results,
    users=users,
    node_types=node_types,
    blue_agent=blue_agent
)
