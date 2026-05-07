from pyvis.network import Network
import json


def visualize_graph(G, results, users, node_types=None, blue_agent=None):
    print("\n🔍 Generating visualization...")

    net = Network(
        height="800px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="black"
    )

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -9000,
          "springLength": 260,
          "springConstant": 0.03,
          "damping": 0.09
        }
      },
      "edges": {
        "smooth": { "type": "continuous" }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)

    timeline = results.get("timeline", [])
    users_final = results.get("users_final", {})
    states_history = results.get("states_history", [])

    # Начальные состояния пользователей
    users_initial = {}
    for k, v in users.items():
        if hasattr(v, 'b'):
            users_initial[str(k)] = {'b': v.b, 'c': v.c, 'e': v.e}
        elif isinstance(v, dict):
            users_initial[str(k)] = v
        else:
            users_initial[str(k)] = {'b': 0, 'c': 0, 'e': 0}

    # Группировка сообщений по рёбрам
    message_transmissions = {}
    for event in timeline:
        key = (event["from"], event["to"])
        message_transmissions.setdefault(key, []).append(event)

    # ---- Узлы ----
    for node in G.nodes():
        node_str = str(node)
        tooltip_lines = [f"━━━━━━━━━━━━━━━━━━━━━━\n🔷 AGENT {node}\n━━━━━━━━━━━━━━━━━━━━━━"]

        ntype = None
        if node_types:
            ntype = node_types.get(node) or node_types.get(str(node))

        if ntype == "U":
            color = "#87CEEB"
            shape = "circle"
            base_size = 40
            tooltip_lines.append("📌 TYPE: USER (Голубой круг)")
        elif ntype == "R":
            color = "#e74c3c"
            shape = "box"
            base_size = 40
            tooltip_lines.append("📌 TYPE: RED AGENT (Красный квадрат)")
        elif ntype == "L":
            color = "#f1c40f"
            shape = "triangle"
            base_size = 40
            tooltip_lines.append("📌 TYPE: LLM AGENT (Жёлтый треугольник)")
        else:
            # автоопределение
            if node in [4, 7, 8, 9]:
                color = "#e74c3c"
                shape = "box"
                base_size = 40
                tooltip_lines.append("📌 TYPE: RED AGENT (Автоопределен)")
            elif node in [10, 11, 12]:
                color = "#f1c40f"
                shape = "triangle"
                base_size = 40
                tooltip_lines.append("📌 TYPE: LLM AGENT (Автоопределен)")
            else:
                color = "#87CEEB"
                shape = "circle"
                base_size = 35
                tooltip_lines.append("📌 TYPE: USER (Автоопределен)")

        tooltip_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        if node_str in users_initial:
            init = users_initial[node_str]
            tooltip_lines.append("📊 INITIAL STATE:")
            tooltip_lines.append(f"   • b: {init.get('b', 0):.4f}")
            tooltip_lines.append(f"   • c: {init.get('c', 0):.4f}")
            tooltip_lines.append(f"   • e: {init.get('e', 0):.4f}")
        if node_str in users_final:
            tooltip_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
            final = users_final[node_str]
            tooltip_lines.append("📊 FINAL STATE:")
            tooltip_lines.append(f"   • b: {final.get('b', 0):.4f}")
            tooltip_lines.append(f"   • c: {final.get('c', 0):.4f}")
            tooltip_lines.append(f"   • e: {final.get('e', 0):.4f}")

        tooltip_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        sent_messages = [e for e in timeline if e["from"] == node]
        received_messages = [e for e in timeline if e["to"] == node]
        tooltip_lines.append(f"📤 SENT: {len(sent_messages)}")
        tooltip_lines.append(f"📥 RECEIVED: {len(received_messages)}")
        tooltip_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        tooltip_lines.append(f"🔗 OUT: {G.out_degree(node)}")
        tooltip_lines.append(f"🔗 IN: {G.in_degree(node)}")
        tooltip_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        tooltip_lines.append("💡 Двойной клик → полная информация")

        net.add_node(
            node,
            label=str(node),
            color=color,
            shape=shape,
            size=base_size,
            title="\n".join(tooltip_lines),
            font={"size": 14, "color": "black", "face": "Arial"}
        )

    # ---- Рёбра ----
    edge_id = 0
    edge_map = {}
    edge_full_info = {}
    edge_messages_by_time = {}

    for u, v, data in G.edges(data=True):
        key = (u, v)
        msgs = message_transmissions.get(key, [])

        full_messages = []
        for msg in msgs:
            t = msg.get('t', 0)
            txt = msg.get('text', '')
            cat = msg.get('category', 'unknown')
            h_val = msg.get('h', 0)
            risk_score = msg.get('risk_score', 0)
            risk_level = msg.get('risk_level', 'UNKNOWN')

            full_messages.append(
                f"<div style='border-bottom:1px solid #ddd; padding:8px; margin-bottom:5px;'>"
                f"<b>━━━ Message t={t} ━━━</b><br>"
                f"<b>📝 Text:</b> {txt}<br>"
                f"<b>🎯 Category:</b> {cat}<br>"
                f"<b>📊 h:</b> {h_val:.4f}<br>"
                f"<b>🤖 Risk Score:</b> {risk_score}<br>"
                f"<b>⚠️ Risk Level:</b> {risk_level}<br>"
                f"</div>"
            )

        edge_full_info[edge_id] = {
            "u": u,
            "v": v,
            "messages": full_messages,
            "total": len(full_messages)
        }

        by_time = {}
        for msg in msgs:
            t = msg.get('t', 0)
            by_time.setdefault(t, []).append({
                "text": msg.get('text', '')[:80],
                "category": msg.get('category', 'unknown'),
                "h": msg.get('h', 0),
                "risk_score": msg.get('risk_score', 0),
                "risk_level": msg.get('risk_level', 'UNKNOWN')
            })
        edge_messages_by_time[edge_id] = by_time

        # Цвет ребра
        if msgs:
            categories = [msg.get('category', '') for msg in msgs]
            if 'threat' in categories or 'manipulative' in categories:
                edge_color = "#e74c3c"
            elif 'neutral' in categories:
                edge_color = "#3498db"
            else:
                edge_color = "#95a5a6"
        else:
            edge_color = "#95a5a6"

        reposts = data.get('reposts', 0)
        risk_sum = data.get('risk_sum', 0)

        net.add_edge(
            u, v, id=edge_id,
            color=edge_color, width=2,
            arrows="to",
            title=f"EDGE {u} → {v}\n📊 Reposts: {reposts}\n📈 Risk Sum: {risk_sum}\n🎯 Avg Risk: {risk_sum/reposts if reposts > 0 else 0:.3f}\n💡 Двойной клик → полная информация"
        )
        edge_map[f"{u},{v}"] = edge_id
        edge_id += 1

    # ---- Таймлайн ----
    timeline_by_time = {}
    for e in timeline:
        t = e["t"]
        timeline_by_time.setdefault(t, []).append(e)

    max_time = max(timeline_by_time.keys()) if timeline_by_time else 0

    # ---- История состояний для узлов ----
    node_states_history = {}
    for node in G.nodes():
        node_str = str(node)
        states = []
        for t_step, snapshot in enumerate(states_history):
            if node_str in snapshot:
                states.append({
                    "t": t_step,
                    "b": snapshot[node_str]["b"],
                    "c": snapshot[node_str]["c"],
                    "e": snapshot[node_str]["e"]
                })
        node_states_history[node_str] = states

    # ---- Сериализация в JSON ----
    timeline_json = json.dumps(timeline_by_time, ensure_ascii=False)
    edge_map_json = json.dumps(edge_map)
    edge_full_info_json = json.dumps(edge_full_info, ensure_ascii=False)
    edge_messages_by_time_json = json.dumps(edge_messages_by_time, ensure_ascii=False)
    node_states_history_json = json.dumps(node_states_history, ensure_ascii=False)

    html = net.generate_html()

    # ---- Кастомный JS ----
    custom_js = f"""
<script>
let timelineData = {timeline_json};
let edgeMap = {edge_map_json};
let edgeFullInfo = {edge_full_info_json};
let edgeMessagesByTime = {edge_messages_by_time_json};
let nodeStatesHistory = {node_states_history_json};

let currentTime = 0;
let animInterval = null;
let settingsVisible = false;

// ---------- Модальное окно для ребра ----------
function showFullInfoEdge(edgeId) {{
    let info = edgeFullInfo[edgeId];
    let modal = document.getElementById("edgeModal");
    let content = document.getElementById("edgeModalContent");
    
    if (!modal) {{
        let modalHtml = `
        <div id="edgeModal" style="display:none; position:fixed; z-index:10000; left:0; top:0;
             width:100%; height:100%; background:rgba(0,0,0,0.6); backdrop-filter:blur(5px);">
            <div style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
                 background:white; border-radius:12px; width:70%; max-width:800px; max-height:80%;
                 box-shadow:0 10px 40px rgba(0,0,0,0.3); display:flex; flex-direction:column;">
                <div style="padding:15px 20px; border-bottom:2px solid #eee; display:flex; 
                     justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; color:#333;">📋 Полная информация о ребре</h3>
                    <button onclick="closeModal('edgeModal')" style="background:none; border:none; 
                            font-size:28px; cursor:pointer; color:#999;">&times;</button>
                </div>
                <div id="edgeModalContent" style="padding:20px; overflow-y:auto; flex:1;
                     font-family:monospace; font-size:12px;"></div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById("edgeModal");
        content = document.getElementById("edgeModalContent");
    }}
    
    if (info && info.messages.length) {{
        content.innerHTML = `<b>🔷 EDGE ${{info.u}} → ${{info.v}}</b><br><hr>
            <b>📊 Всего сообщений:</b> ${{info.total}}<br><br>
            <div style="max-height:500px; overflow-y:auto;">${{info.messages.join('')}}</div>`;
    }} else {{
        content.innerHTML = "<i>На этом ребре нет сообщений</i>";
    }}
    modal.style.display = "block";
}}

// ---------- Модальное окно для узла (с историей состояний) ----------
function showFullInfoNode(nodeId) {{
    let modal = document.getElementById("nodeModal");
    let content = document.getElementById("nodeModalContent");
    
    if (!modal) {{
        let modalHtml = `
        <div id="nodeModal" style="display:none; position:fixed; z-index:10000; left:0; top:0;
             width:100%; height:100%; background:rgba(0,0,0,0.6); backdrop-filter:blur(5px);">
            <div style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
                 background:white; border-radius:12px; width:70%; max-width:800px; max-height:80%;
                 box-shadow:0 10px 40px rgba(0,0,0,0.3); display:flex; flex-direction:column;">
                <div style="padding:15px 20px; border-bottom:2px solid #eee; display:flex; 
                     justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; color:#333;">📋 Информация об узле</h3>
                    <button onclick="closeModal('nodeModal')" style="background:none; border:none; 
                            font-size:28px; cursor:pointer; color:#999;">&times;</button>
                </div>
                <div id="nodeModalContent" style="padding:20px; overflow-y:auto; flex:1;
                     font-family:monospace; font-size:12px;"></div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById("nodeModal");
        content = document.getElementById("nodeModalContent");
    }}
    
    let node = network.body.data.nodes.get(nodeId);
    let states = nodeStatesHistory[nodeId] || [];
    
    let html = `<b>🔷 УЗЕЛ: ${{nodeId}}</b><br><hr>`;
    html += `<b>📌 Тип:</b> ${{node.label || 'USER'}}<br>`;
    html += `<b>🎨 Цвет:</b> ${{node.color}}<br>`;
    html += `<b>📊 Степень:</b> out=${{node.out || 0}}, in=${{node.in || 0}}<br><br>`;
    
    html += `<hr><b>📈 ИСТОРИЯ СОСТОЯНИЙ (b, c, e) по времени:</b><br><br>`;
    html += `<div style="max-height:250px; overflow-y:auto;">`;
    if (states.length > 0) {{
        html += `<table style="width:100%; border-collapse:collapse;">`;
        html += `<tr style="background:#f0f0f0;"><th>t</th><th>b</th><th>c</th><th>e</th></tr>`;
        for (let s of states) {{
            html += `<tr><td>${{s.t}}</td><td>${{s.b.toFixed(4)}}</td><td>${{s.c.toFixed(4)}}</td><td>${{s.e.toFixed(4)}}</td></tr>`;
        }}
        html += `</table>`;
    }} else {{
        html += `<i>Нет данных об истории состояний</i>`;
    }}
    html += `</div><br><hr>`;
    
    // Собираем сообщения
    let sentMsgs = [];
    let receivedMsgs = [];
    for (let t in timelineData) {{
        for (let e of timelineData[t]) {{
            if (e.from == nodeId) sentMsgs.push(e);
            if (e.to == nodeId) receivedMsgs.push(e);
        }}
    }}
    
    html += `<b>📤 ОТПРАВЛЕННЫЕ СООБЩЕНИЯ:</b><br><br>`;
    html += `<div style="max-height:200px; overflow-y:auto;">`;
    if (sentMsgs.length > 0) {{
        for (let msg of sentMsgs) {{
            let shortText = msg.text.length > 100 ? msg.text.substring(0, 100) + '...' : msg.text;
            html += `<div style="border:1px solid #ddd; padding:8px; margin-bottom:5px; border-radius:5px;">`;
            html += `<b>t=${{msg.t}} → ${{msg.to}}</b><br>`;
            html += `📝 ${{shortText}}<br>`;
            html += `🏷️ ${{msg.category}} | 📊 h=${{msg.h.toFixed(4)}}<br>`;
            html += `🤖 Risk: ${{msg.risk_score}} (${{msg.risk_level}})`;
            html += `</div>`;
        }}
    }} else {{
        html += `<i>Нет отправленных сообщений</i>`;
    }}
    html += `</div><br><hr>`;
    
    html += `<b>📥 ПОЛУЧЕННЫЕ СООБЩЕНИЯ:</b><br><br>`;
    html += `<div style="max-height:200px; overflow-y:auto;">`;
    if (receivedMsgs.length > 0) {{
        for (let msg of receivedMsgs) {{
            let shortText = msg.text.length > 100 ? msg.text.substring(0, 100) + '...' : msg.text;
            html += `<div style="border:1px solid #ddd; padding:8px; margin-bottom:5px; border-radius:5px;">`;
            html += `<b>t=${{msg.t}} ← ${{msg.from}}</b><br>`;
            html += `📝 ${{shortText}}<br>`;
            html += `🏷️ ${{msg.category}} | 📊 h=${{msg.h.toFixed(4)}}<br>`;
            html += `🤖 Risk: ${{msg.risk_score}} (${{msg.risk_level}})`;
            html += `</div>`;
        }}
    }} else {{
        html += `<i>Нет полученных сообщений</i>`;
    }}
    html += `</div>`;
    
    content.innerHTML = html;
    modal.style.display = "block";
}}

function closeModal(modalId) {{
    let modal = document.getElementById(modalId);
    if (modal) modal.style.display = "none";
}}

// ---------- Обновление тултипов рёбер по времени ----------
function updateEdgeTooltip(edgeId, time) {{
    let edges = network.body.data.edges;
    let edge = edges.get(edgeId);
    if (!edge) return;
    let msgs = (edgeMessagesByTime[edgeId] || {{}})[time] || [];
    let lines = [];
    lines.push("━━━━━━━━━━━━━━━━━━━━━━");
    lines.push("EDGE " + edge.from + " → " + edge.to);
    lines.push("⏰ ВРЕМЯ: " + time);
    if (msgs.length) {{
        lines.push("📨 СООБЩЕНИЙ: " + msgs.length);
        for (let i=0; i<msgs.length; i++) {{
            lines.push("────────────────────");
            lines.push("📝: " + msgs[i].text.substring(0, 50));
            lines.push("🏷️: " + msgs[i].category);
            lines.push("🤖 Risk: " + msgs[i].risk_score + " (" + msgs[i].risk_level + ")");
        }}
    }} else {{
        lines.push("📭 Нет сообщений");
    }}
    lines.push("━━━━━━━━━━━━━━━━━━━━━━");
    lines.push("💡 Двойной клик → полная информация");
    edges.update({{ id: edgeId, title: lines.join("\\n") }});
}}

function updateAllTooltips(time) {{
    for (let key in edgeMap) {{
        updateEdgeTooltip(edgeMap[key], time);
    }}
}}

function resetAllEdges() {{
    let edges = network.body.data.edges;
    let all = edges.get();
    for (let i=0; i<all.length; i++) {{
        edges.update({{ id: all[i].id, color: "#95a5a6", width: 2 }});
    }}
}}

function highlightEdge(from, to, color) {{
    let eid = edgeMap[from+","+to];
    if (eid !== undefined) {{
        network.body.data.edges.update({{ id: eid, color: color, width: 4 }});
    }}
}}

function updateByTime(time) {{
    resetAllEdges();
    let events = timelineData[time] || [];
    for (let e of events) {{
        let col = "#3498db";
        if (e.category === "threat" || e.category === "manipulative") {{
            col = "#e74c3c";
        }}
        highlightEdge(e.from, e.to, col);
    }}
    updateAllTooltips(time);
    document.getElementById("timeLabel").innerHTML = "⏰ TIME: " + time;
    document.getElementById("timeSlider").value = time;
}}

// ---------- Анимация ----------
function playAnimation() {{
    if (animInterval) {{
        clearInterval(animInterval);
        animInterval = null;
        document.getElementById("playBtn").innerHTML = "▶ Play";
        return;
    }}
    document.getElementById("playBtn").innerHTML = "⏸ Pause";
    animInterval = setInterval(() => {{
        if (currentTime >= {max_time}) {{
            clearInterval(animInterval);
            animInterval = null;
            document.getElementById("playBtn").innerHTML = "▶ Play";
            return;
        }}
        currentTime++;
        updateByTime(currentTime);
    }}, 800);
}}

function resetAnimation() {{
    if (animInterval) {{ clearInterval(animInterval); animInterval = null; }}
    currentTime = 0;
    updateByTime(0);
    document.getElementById("playBtn").innerHTML = "▶ Play";
}}

function onTimeChange(val) {{
    if (animInterval) {{
        clearInterval(animInterval);
        animInterval = null;
        document.getElementById("playBtn").innerHTML = "▶ Play";
    }}
    currentTime = parseInt(val);
    updateByTime(currentTime);
}}

// ---------- Настройки (размер узлов и длина рёбер) ----------
function toggleSettings() {{
    let panel = document.getElementById("settingsPanel");
    settingsVisible = !settingsVisible;
    panel.style.display = settingsVisible ? "block" : "none";
}}

function updateNodeSize(val) {{
    let nodes = network.body.data.nodes;
    let all = nodes.get();
    for (let n of all) nodes.update({{ id: n.id, size: parseInt(val) }});
    document.getElementById("nodeSizeValue").innerHTML = val;
}}

function updateEdgeDistance(val) {{
    network.setOptions({{ physics: {{ barnesHut: {{ springLength: parseInt(val) }} }} }});
    document.getElementById("edgeDistanceValue").innerHTML = val;
}}

// ---------- Инициализация ----------
network.on("stabilizationIterationsDone", () => {{
    updateByTime(0);
    network.on("doubleClick", (params) => {{
        if (params.edges.length) {{
            showFullInfoEdge(params.edges[0]);
        }} else if (params.nodes.length) {{
            showFullInfoNode(params.nodes[0]);
        }}
    }});
}});

// Закрытие модальных окон по клику вне области
document.addEventListener('click', function(e) {{
    let edgeModal = document.getElementById('edgeModal');
    let nodeModal = document.getElementById('nodeModal');
    if (e.target === edgeModal) edgeModal.style.display = 'none';
    if (e.target === nodeModal) nodeModal.style.display = 'none';
}});
</script>

<!-- Панель настроек (слева внизу) -->
<div style="position:fixed; bottom:20px; left:20px; z-index:999;">
  <button onclick="toggleSettings()" style="background:#34495e; color:white; border:none;
          padding:12px 20px; border-radius:8px; cursor:pointer; font-weight:bold;">
    ⚙ НАСТРОЙКИ
  </button>
  <div id="settingsPanel" style="display:none; position:fixed; bottom:80px; left:20px;
       background:white; padding:15px; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.3);
       min-width:220px; z-index:1000;">
    <div style="margin-bottom:15px;">
      <div style="font-weight:bold;">📏 Размер узлов</div>
      <input type="range" min="10" max="80" value="40" oninput="updateNodeSize(this.value)" style="width:100%;">
      <div style="font-size:12px;">Текущий: <span id="nodeSizeValue">40</span> px</div>
    </div>
    <div>
      <div style="font-weight:bold;">📏 Дистанция рёбер</div>
      <input type="range" min="80" max="800" value="260" oninput="updateEdgeDistance(this.value)" style="width:100%;">
      <div style="font-size:12px;">Текущий: <span id="edgeDistanceValue">260</span> px</div>
    </div>
  </div>
</div>

<!-- Панель таймлайна (справа внизу) -->
<div style="position:fixed; bottom:20px; right:20px; background:white; padding:15px 20px;
     border-radius:12px; box-shadow:0 0 15px rgba(0,0,0,0.3); font-family:Arial; z-index:999;">
  <div style="text-align:center; margin-bottom:10px;"><b>📊 TIMELINE</b></div>
  <div style="display:flex; gap:10px; align-items:center;">
    <button id="playBtn" onclick="playAnimation()" style="background:#3498db; color:white; border:none;
            padding:8px 16px; border-radius:6px; cursor:pointer;">▶ Play</button>
    <button onclick="resetAnimation()" style="background:#e74c3c; color:white; border:none;
            padding:8px 16px; border-radius:6px; cursor:pointer;">⏮ Reset</button>
    <input type="range" id="timeSlider" min="0" max="{max_time}" value="0"
           onchange="onTimeChange(this.value)" style="width:350px;">
  </div>
  <div id="timeLabel" style="margin-top:10px; text-align:center;">⏰ TIME: 0</div>
</div>

<style>
  .vis-tooltip {{ 
    background: rgba(0,0,0,0.95); 
    color: #fff; 
    padding: 12px;
    border-radius: 8px; 
    font-size: 11px; 
    font-family: monospace; 
    max-width: 500px; 
    white-space: pre-line;
    z-index: 1000;
  }}
  ::-webkit-scrollbar {{
    width: 8px;
  }}
  ::-webkit-scrollbar-track {{
    background: #f1f1f1;
    border-radius: 4px;
  }}
  ::-webkit-scrollbar-thumb {{
    background: #888;
    border-radius: 4px;
  }}
  ::-webkit-scrollbar-thumb:hover {{
    background: #555;
  }}
</style>
"""

    html = html.replace("</body>", custom_js + "</body>")

    with open("network_visualization_pro.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("\n✅ network_visualization_pro.html saved")
    print(f"📊 Максимальное время: {max_time}")
    print(f"🔗 Всего рёбер: {edge_id}")