# pyright: reportUndefinedVariable=false
from pyvis.network import Network
import json

def visualize_graph(G, results, users, node_types=None, blue_agent=None, output_path="network_visualization_pro.html"):
    print("\n🔍 Generating visualization...")

    net = Network(height="800px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
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
      "edges": { "smooth": { "type": "continuous" } },
      "interaction": { "hover": true, "tooltipDelay": 100 }
    }
    """)

    timeline = results.get("timeline", [])
    users_final = results.get("users_final", {})
    states_history = results.get("states_history", [])

    users_initial = {}
    for k, v in users.items():
        if hasattr(v, 'b'):
            users_initial[str(k)] = {'b': v.b, 'c': v.c, 'e': v.e}
        elif isinstance(v, dict):
            users_initial[str(k)] = v
        else:
            users_initial[str(k)] = {'b': 0, 'c': 0, 'e': 0}

    message_transmissions = {}
    for ev in timeline:
        key = (ev["from"], ev["to"])
        message_transmissions.setdefault(key, []).append(ev)

    # ---- Узлы ----
    for node in G.nodes():
        node_str = str(node)
        tooltip_lines = [f"━━━━━━━━━━━━━━━━━━━━━━\n🔷 AGENT {node}\n━━━━━━━━━━━━━━━━━━━━━━"]

        ntype = None
        if node_types:
            ntype = node_types.get(node) or node_types.get(node_str)

        if ntype == "U":
            color, shape, base_size = "#87CEEB", "circle", 40
            tooltip_lines.append("📌 TYPE: USER (Голубой круг)")
        elif ntype == "R":
            color, shape, base_size = "#e74c3c", "box", 40
            tooltip_lines.append("📌 TYPE: RED AGENT (Красный квадрат)")
        elif ntype == "L":
            color, shape, base_size = "#f1c40f", "triangle", 40
            tooltip_lines.append("📌 TYPE: LLM AGENT (Жёлтый треугольник)")
        else:
            if node in (4,7,8,9):
                color, shape, base_size = "#e74c3c", "box", 40
                tooltip_lines.append("📌 TYPE: RED AGENT (Автоопределен)")
            elif node in (10,11,12):
                color, shape, base_size = "#f1c40f", "triangle", 40
                tooltip_lines.append("📌 TYPE: LLM AGENT (Автоопределен)")
            else:
                color, shape, base_size = "#87CEEB", "circle", 35
                tooltip_lines.append("📌 TYPE: USER (Автоопределен)")

        tooltip_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        if node_str in users_initial:
            init = users_initial[node_str]
            tooltip_lines.append("📊 INITIAL STATE:")
            tooltip_lines.append(f"   • b: {init.get('b',0):.4f}")
            tooltip_lines.append(f"   • c: {init.get('c',0):.4f}")
            tooltip_lines.append(f"   • e: {init.get('e',0):.4f}")
        if node_str in users_final:
            tooltip_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
            fin = users_final[node_str]
            tooltip_lines.append("📊 FINAL STATE:")
            tooltip_lines.append(f"   • b: {fin.get('b',0):.4f}")
            tooltip_lines.append(f"   • c: {fin.get('c',0):.4f}")
            tooltip_lines.append(f"   • e: {fin.get('e',0):.4f}")

        tooltip_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        sent = sum(1 for e in timeline if e["from"]==node)
        recv = sum(1 for e in timeline if e["to"]==node)
        tooltip_lines.append(f"📤 SENT: {sent}")
        tooltip_lines.append(f"📥 RECEIVED: {recv}")
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
            scaling={"min": 10, "max": 100},
            title="\n".join(tooltip_lines),
            font={"size": 14, "color": "black", "face": "Arial"}
        )

    # ---- Рёбра ----
    edge_id = 0
    edge_map = {}
    edge_full_info = {}
    edge_messages_by_time = {}

    for u, v, data in G.edges(data=True):
        msgs = message_transmissions.get((u, v), [])
        full_msgs = []
        for m in msgs:
            full_msgs.append(
                f"<div style='border-bottom:1px solid #ddd; padding:8px; margin-bottom:5px;'>"
                f"<b>━━━ Message t={m.get('t',0)} ━━━</b><br>"
                f"<b>📝 Text:</b> {m.get('text','')}<br>"
                f"<b>🎯 Category:</b> {m.get('category','unknown')}<br>"
                f"<b>📊 h:</b> {m.get('h',0):.4f}<br>"
                f"<b>🤖 Risk Score:</b> {m.get('risk_score',0)}<br>"
                f"<b>⚠️ Risk Level:</b> {m.get('risk_level','UNKNOWN')}<br></div>"
            )
        edge_full_info[edge_id] = {"u": u, "v": v, "messages": full_msgs, "total": len(full_msgs)}

        by_time = {}
        for m in msgs:
            t = m.get('t',0)
            by_time.setdefault(t, []).append({
                "text": m.get('text','')[:80],
                "category": m.get('category','unknown'),
                "h": m.get('h',0),
                "risk_score": m.get('risk_score',0),
                "risk_level": m.get('risk_level','UNKNOWN')
            })
        edge_messages_by_time[edge_id] = by_time

        if msgs:
            cats = [m.get('category','') for m in msgs]
            if any(c in ('threat','manipulative') for c in cats):
                edge_color = "#e74c3c"
            elif 'neutral' in cats:
                edge_color = "#3498db"
            else:
                edge_color = "#95a5a6"
        else:
            edge_color = "#95a5a6"

        reposts = data.get('reposts',0)
        risk_sum = data.get('risk_sum',0)
        avg_risk = risk_sum/reposts if reposts>0 else 0

        net.add_edge(u, v, id=edge_id, color=edge_color, width=2, arrows="to",
                     title=f"EDGE {u}→{v}\n📊 Reposts: {reposts}\n📈 Risk Sum: {risk_sum}\n🎯 Avg Risk: {avg_risk:.3f}\n💡 Двойной клик → полная информация")
        edge_map[f"{u},{v}"] = edge_id
        edge_id += 1

    # ---- Таймлайн ----
    timeline_by_time = {}
    for e in timeline:
        t = e["t"]
        timeline_by_time.setdefault(t, []).append(e)
    max_time = max(timeline_by_time.keys()) if timeline_by_time else 0

    # ---- История узлов ----
    node_full_history = {}
    for node in G.nodes():
        node_str = str(node)
        history = []
        if node_str in users_initial:
            history.append({
                "t": 0,
                "b": users_initial[node_str].get('b',0),
                "c": users_initial[node_str].get('c',0),
                "e": users_initial[node_str].get('e',0)
            })
        for step, snapshot in enumerate(states_history, start=1):
            if node_str in snapshot:
                history.append({
                    "t": step,
                    "b": snapshot[node_str]["b"],
                    "c": snapshot[node_str]["c"],
                    "e": snapshot[node_str]["e"]
                })
        if not history and node_str in users_final:
            history.append({
                "t": max_time,
                "b": users_final[node_str].get('b',0),
                "c": users_final[node_str].get('c',0),
                "e": users_final[node_str].get('e',0)
            })
        node_full_history[node_str] = history

    timeline_json = json.dumps(timeline_by_time, ensure_ascii=False)
    edge_map_json = json.dumps(edge_map)
    edge_full_info_json = json.dumps(edge_full_info, ensure_ascii=False)
    edge_messages_by_time_json = json.dumps(edge_messages_by_time, ensure_ascii=False)
    node_history_json = json.dumps(node_full_history, ensure_ascii=False)

    html = net.generate_html()

    custom_js = f"""
<script>
let timelineData = {timeline_json};
let edgeMap = {edge_map_json};
let edgeFullInfo = {edge_full_info_json};
let edgeMessagesByTime = {edge_messages_by_time_json};
let nodeStatesHistory = {node_history_json};

console.log("History loaded:", nodeStatesHistory);

let currentTime = 0;
let animInterval = null;
let settingsVisible = false;

function showFullInfoEdge(edgeId) {{
    let info = edgeFullInfo[edgeId];
    let modal = document.getElementById("edgeModal");
    let content = document.getElementById("edgeModalContent");
    if (!modal) {{
        let modalHtml = `
        <div id="edgeModal" style="display:none; position:fixed; z-index:10000; left:0; top:0;
             width:100%; height:100%; background:rgba(0,0,0,0.6); backdrop-filter:blur(5px);">
            <div style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
                 background:white; border-radius:12px; width:70%%; max-width:800px; max-height:80%%;
                 box-shadow:0 10px 40px rgba(0,0,0,0.3); display:flex; flex-direction:column;">
                <div style="padding:15px 20px; border-bottom:2px solid #eee; display:flex; 
                     justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">📋 Полная информация о ребре</h3>
                    <button onclick="closeModal('edgeModal')" style="background:none; border:none; font-size:28px; cursor:pointer;">&times;</button>
                </div>
                <div id="edgeModalContent" style="padding:20px; overflow-y:auto; flex:1; font-family:monospace; font-size:12px;"></div>
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

function showFullInfoNode(nodeId) {{
    let modal = document.getElementById("nodeModal");
    let content = document.getElementById("nodeModalContent");
    if (!modal) {{
        let modalHtml = `
        <div id="nodeModal" style="display:none; position:fixed; z-index:10000; left:0; top:0;
             width:100%; height:100%; background:rgba(0,0,0,0.6); backdrop-filter:blur(5px);">
            <div style="position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
                 background:white; border-radius:12px; width:75%; max-width:1000px; max-height:85%;
                 box-shadow:0 10px 40px rgba(0,0,0,0.3); display:flex; flex-direction:column;">
                <div style="padding:15px 20px; border-bottom:2px solid #eee; display:flex; 
                     justify-content:space-between; align-items:center;">
                    <h2 style="margin:0;">🔷 NODE ${{nodeId}}</h2>
                    <button onclick="closeModal('nodeModal')" style="background:none; border:none; font-size:28px; cursor:pointer;">&times;</button>
                </div>
                <div id="nodeModalContent" style="padding:20px; overflow-y:auto; flex:1; font-family:monospace; font-size:13px;"></div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById("nodeModal");
        content = document.getElementById("nodeModalContent");
    }}

    let states = nodeStatesHistory[String(nodeId)];
    if (!states || states.length === 0) {{
        content.innerHTML = "<i>Нет истории состояний для этого узла</i>";
        modal.style.display = "block";
        return;
    }}

    let html = `<h3>📈 UserState History (b, c, e)</h3>`;
    html += `<table style="width:100%; border-collapse:collapse; text-align:center;">
                <thead>
                    <tr style="background:#f0f0f0; border-bottom:2px solid #ccc;">
                        <th style="padding:10px;">t</th>
                        <th style="padding:10px;">b</th>
                        <th style="padding:10px;">c</th>
                        <th style="padding:10px;">e</th>
                    </tr>
                </thead>
                <tbody>`;
    for (let s of states) {{
        html += `<tr style="border-bottom:1px solid #ddd;">
                    <td style="padding:8px;">${s.t}</td>
                    <td style="padding:8px;">${Number(s.b).toFixed(6)}</td>
                    <td style="padding:8px;">${Number(s.c).toFixed(6)}</td>
                    <td style="padding:8px;">${Number(s.e).toFixed(6)}</td>
                 </tr>`;
    }}
    html += `</tbody>们</div>`;
    content.innerHTML = html;
    modal.style.display = "block";
}}

function closeModal(modalId) {{
    let modal = document.getElementById(modalId);
    if(modal) modal.style.display = "none";
}}

function updateEdgeTooltip(edgeId, time) {{
    let edges = network.body.data.edges;
    let edge = edges.get(edgeId);
    if(!edge) return;
    let msgs = (edgeMessagesByTime[edgeId] || {{}})[time] || [];
    let lines = ["━━━━━━━━━━━━━━━━━━━━━━", "EDGE " + edge.from + " → " + edge.to, "⏰ ВРЕМЯ: " + time];
    if(msgs.length) {{
        lines.push("📨 СООБЩЕНИЙ: " + msgs.length);
        for(let i=0;i<msgs.length;i++){{
            lines.push("────────────────────");
            lines.push("📝: " + msgs[i].text.substring(0,50));
            lines.push("🏷️: " + msgs[i].category);
            lines.push("🤖 Risk: " + msgs[i].risk_score + " (" + msgs[i].risk_level + ")");
        }}
    }} else {{
        lines.push("📭 Нет сообщений");
    }}
    lines.push("━━━━━━━━━━━━━━━━━━━━━━","💡 Двойной клик → полная информация");
    edges.update({{ id: edgeId, title: lines.join("\\n") }});
}}

function updateAllTooltips(time) {{
    for(let key in edgeMap) updateEdgeTooltip(edgeMap[key], time);
}}

function resetAllEdges() {{
    let edges = network.body.data.edges;
    let all = edges.get();
    for(let e of all) edges.update({{ id: e.id, color: "#95a5a6", width: 2 }});
}}

function highlightEdge(from, to, color) {{
    let eid = edgeMap[from+","+to];
    if(eid !== undefined) network.body.data.edges.update({{ id: eid, color: color, width: 4 }});
}}

function updateByTime(time) {{
    resetAllEdges();
    let events = timelineData[time] || [];
    for(let e of events){{
        let col = (e.category==="threat"||e.category==="manipulative") ? "#e74c3c" : "#3498db";
        highlightEdge(e.from, e.to, col);
    }}
    updateAllTooltips(time);
    document.getElementById("timeLabel").innerHTML = "⏰ TIME: " + time;
    document.getElementById("timeSlider").value = time;
}}

function playAnimation() {{
    if(animInterval){{
        clearInterval(animInterval); animInterval=null;
        document.getElementById("playBtn").innerHTML = "▶ Play";
        return;
    }}
    document.getElementById("playBtn").innerHTML = "⏸ Pause";
    animInterval = setInterval(() => {{
        if(currentTime >= {max_time}){{
            clearInterval(animInterval); animInterval=null;
            document.getElementById("playBtn").innerHTML = "▶ Play";
            return;
        }}
        currentTime++;
        updateByTime(currentTime);
    }}, 800);
}}

function resetAnimation() {{
    if(animInterval){{ clearInterval(animInterval); animInterval=null; }}
    currentTime=0; updateByTime(0);
    document.getElementById("playBtn").innerHTML = "▶ Play";
}}

function onTimeChange(val){{
    if(animInterval){{ clearInterval(animInterval); animInterval=null; document.getElementById("playBtn").innerHTML = "▶ Play"; }}
    currentTime = parseInt(val);
    updateByTime(currentTime);
}}

function toggleSettings(){{
    let panel = document.getElementById("settingsPanel");
    settingsVisible = !settingsVisible;
    panel.style.display = settingsVisible ? "block" : "none";
}}

function updateNodeSize(val){{
    let nodes = network.body.data.nodes;
    let allNodes = nodes.get();
    for(let n of allNodes){{
        nodes.update({{ id: n.id, size: Number(val), font: {{ size: Math.max(12, Number(val) * 0.35) }} }});
    }}
    network.redraw();
    document.getElementById("nodeSizeValue").innerHTML = val;
}}

function updateEdgeDistance(val){{
    network.setOptions({{ physics: {{ barnesHut: {{ springLength: parseInt(val) }} }} }});
    document.getElementById("edgeDistanceValue").innerHTML = val;
}}

network.once("stabilizationIterationsDone", function() {{
    updateByTime(0);
}});

network.on("doubleClick", function(params) {{
    if (params.nodes.length > 0) {{
        showFullInfoNode(params.nodes[0]);
    }} else if (params.edges.length > 0) {{
        showFullInfoEdge(params.edges[0]);
    }}
}});

document.addEventListener('click', function(e){{
    let em = document.getElementById('edgeModal');
    let nm = document.getElementById('nodeModal');
    if(e.target===em) em.style.display='none';
    if(e.target===nm) nm.style.display='none';
}});
</script>

<!-- Панель настроек и таймлайна (оставляем как было) -->
<div style="position:fixed; bottom:20px; left:20px; z-index:999;">
  <button onclick="toggleSettings()" style="background:#34495e; color:white; border:none; padding:12px 20px; border-radius:8px; cursor:pointer;">⚙ НАСТРОЙКИ</button>
  <div id="settingsPanel" style="display:none; position:fixed; bottom:80px; left:20px; background:white; padding:15px; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.3); min-width:220px;">
    <div><div>📏 Размер узлов</div><input type="range" min="10" max="80" value="40" oninput="updateNodeSize(this.value)" style="width:100%;"><div>Текущий: <span id="nodeSizeValue">40</span> px</div></div>
    <div style="margin-top:10px;"><div>📏 Дистанция рёбер</div><input type="range" min="80" max="800" value="260" oninput="updateEdgeDistance(this.value)" style="width:100%;"><div>Текущий: <span id="edgeDistanceValue">260</span> px</div></div>
  </div>
</div>

<div style="position:fixed; bottom:20px; right:20px; background:white; padding:15px 20px; border-radius:12px; box-shadow:0 0 15px rgba(0,0,0,0.3);">
  <div style="text-align:center; margin-bottom:10px;"><b>📊 TIMELINE</b></div>
  <div style="display:flex; gap:10px; align-items:center;">
    <button id="playBtn" onclick="playAnimation()" style="background:#3498db; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;">▶ Play</button>
    <button onclick="resetAnimation()" style="background:#e74c3c; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;">⏮ Reset</button>
    <input type="range" id="timeSlider" min="0" max="{max_time}" value="0" onchange="onTimeChange(this.value)" style="width:350px;">
  </div>
  <div id="timeLabel" style="margin-top:10px; text-align:center;">⏰ TIME: 0</div>
</div>

<style>
  .vis-tooltip {{ background: rgba(0,0,0,0.95); color: #fff; padding: 12px; border-radius: 8px; font-size: 11px; font-family: monospace; max-width: 500px; white-space: pre-line; z-index: 1000; }}
  ::-webkit-scrollbar {{ width: 8px; }}
  ::-webkit-scrollbar-track {{ background: #f1f1f1; border-radius: 4px; }}
  ::-webkit-scrollbar-thumb {{ background: #888; border-radius: 4px; }}
  table {{ font-size: 12px; }}
  th {{ position: sticky; top: 0; z-index: 10; }}
</style>
"""

    html = html.replace("</body>", custom_js + "</body>")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ {output_path} saved")
    print(f"📊 Максимальное время: {max_time}")
    print(f"🔗 Всего рёбер: {edge_id}")