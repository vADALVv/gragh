# run.py
from graph_structure import create_graph
from simulation import simulate_diffusion
from visualization import visualize_graph
from blue_agent import BlueAgent

from collections import defaultdict
import json
from tqdm import tqdm
import networkx as nx
import os


N_USERS = 11
N_RED = 5
N_LLM = 0
AVG_DEGREE = 3
T_STEPS = 17

MESSAGES_PATH = r"C:\Users\Vlada\Desktop\llm_attaks\graph\data\messages.json"

# =====================================================
# НАСТРОЙКИ ПУТЕЙ ДЛЯ СОХРАНЕНИЯ
# =====================================================

OUTPUT_DIR = "results"
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Создаёт папку если её нет
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "simulation_result.json")
VIZ_PATH = os.path.join(OUTPUT_DIR, "network_visualization_pro.html")



# =====================================================
# GRAPH + SIMULATION
# =====================================================

print("=" * 50)
print("🔧 CREATING GRAPH")
print("=" * 50)
print(f"📁 Results will be saved to: {OUTPUT_DIR}")

# Проверяем существование файла с сообщениями
if not os.path.exists(MESSAGES_PATH):
    print(f"❌ Error: Messages file not found at {MESSAGES_PATH}")
    exit(1)

G, users, node_types = create_graph(
    num_u=N_USERS,
    num_r=N_RED,
    num_l=N_LLM,
    avg_degree=AVG_DEGREE
)

print(f"✅ Graph created:")
print(f"   - Total nodes: {G.number_of_nodes()}")
print(f"   - Total edges: {G.number_of_edges()}")
print(f"   - Node types: {dict(list(node_types.items())[:5])}...")

print("\n" + "=" * 50)
print("🔄 RUNNING SIMULATION")
print("=" * 50)

results = simulate_diffusion(
    G=G,
    users=users,
    node_types=node_types,
    T_steps=T_STEPS,
    messages_path=MESSAGES_PATH
)

timeline = results["timeline"]
states_history = results.get("states_history", [])
print(f"\n✅ Simulation complete:")
print(f"   - Timeline events: {len(timeline)}")
print(f"   - States snapshots: {len(states_history)}")
print(f"   - Final users: {len(results['users_final'])}")


# =====================================================
# BLUE AGENT
# =====================================================

print("\n" + "=" * 50)
print("🤖 RUNNING BLUE AGENT ANALYSIS")
print("=" * 50)

blue_agent = BlueAgent()

# Анализируем каждое сообщение
for event in tqdm(timeline, desc="Risk analysis"):
    score, level = blue_agent.process_event(event["text"])
    event["risk_score"] = score
    event["risk_level"] = level

print(f"✅ Blue agent analysis complete:")
global_summary = blue_agent.global_summary()
print(f"   - Global risk score: {global_summary['global_risk_score']:.4f}")
print(f"   - Global risk level: {global_summary['global_risk_level']}")


# =====================================================
# EDGE METRICS
# =====================================================

print("\n" + "=" * 50)
print("📊 CALCULATING EDGE METRICS")
print("=" * 50)

edge_counts = defaultdict(int)
edge_risk = defaultdict(float)

for e in timeline:
    k = (e["from"], e["to"])
    edge_counts[k] += 1
    edge_risk[k] += e["h"]

edge_metrics = {
    f"{u}->{v}": {
        "reposts": edge_counts[(u, v)],
        "risk_sum": edge_risk[(u, v)]
    }
    for (u, v) in edge_counts
}

print(f"✅ Edge metrics calculated:")
print(f"   - Total edges with activity: {len(edge_metrics)}")


# =====================================================
# SAVE OUTPUT
# =====================================================

print("\n" + "=" * 50)
print("💾 SAVING RESULTS")
print("=" * 50)

# Подготовка данных для сохранения
nodes_final = {}
for k, v in results["users_final"].items():
    if hasattr(v, 'b'):
        nodes_final[str(k)] = {"b": v.b, "c": v.c, "e": v.e}
    elif isinstance(v, dict):
        nodes_final[str(k)] = v
    else:
        nodes_final[str(k)] = {"b": 0, "c": 0, "e": 0}

# Сохраняем все данные в output
output = {
    "nodes": nodes_final,
    "node_types": node_types,  # Сохраняем типы узлов
    "states_history": states_history,  # Сохраняем историю состояний
    "edges": edge_metrics,
    "timeline": timeline,
    "blue_agent": global_summary,
    "simulation_params": {
        "n_users": N_USERS,
        "n_red": N_RED,
        "n_llm": N_LLM,
        "avg_degree": AVG_DEGREE,
        "t_steps": T_STEPS,
        "total_events": len(timeline)
    }
}

try:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ Results saved to: {OUTPUT_PATH}")
    file_size = len(json.dumps(output)) / 1024
    print(f"   - File size: {file_size:.2f} KB")
except Exception as e:
    print(f"❌ Error saving file: {e}")
    exit(1)


# =====================================================
# VISUALIZATION
# =====================================================

print("\n" + "=" * 50)
print("🎨 GENERATING VISUALIZATION")
print("=" * 50)

# Временно меняем глобальную переменную visualize_graph, чтобы она сохраняла в нужную папку
# Для этого нужно также изменить файл visualization.py или передать параметр

try:
    # Убеждаемся, что node_types передаются правильно
    visualize_graph(
        G=G,
        results=results,
        users=users,
        node_types=node_types,
        blue_agent=blue_agent,
        output_path=VIZ_PATH  # Добавляем параметр с путем для сохранения
    )
    print(f"✅ Visualization generated successfully: {VIZ_PATH}")
except Exception as e:
    print(f"❌ Error generating visualization: {e}")
    print("   Continuing anyway...")

print("\n" + "=" * 50)
print("✅ ALL DONE!")
print("=" * 50)
print(f"\n📁 Output files:")
print(f"   - Simulation data: {OUTPUT_PATH}")
print(f"   - Visualization: {VIZ_PATH}")
print(f"\n📊 Summary:")
print(f"   - Total users: {N_USERS + N_RED + N_LLM}")
print(f"   - Red agents: {N_RED}")
print(f"   - Timeline events: {len(timeline)}")
print(f"   - States snapshots: {len(states_history)}")
if states_history:
    print(f"   - Time range: 0 to {len(states_history)-1}")
print(f"\n💡 To view the visualization, open {VIZ_PATH} in your browser")