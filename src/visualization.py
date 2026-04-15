from pyvis.network import Network
import json


def visualize_graph(G, results, users, node_types=None, blue_agent=None):

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
    users_initial = {str(k): v for k, v in users.items()}

    # -------------------------
    # группировка по ребрам
    # -------------------------
    message_transmissions = {}
    for event in timeline:
        key = (event["from"], event["to"])
        message_transmissions.setdefault(key, []).append(event)

    # -------------------------
    # NODES
    # -------------------------
    for node in G.nodes():
        node_str = str(node)
        tooltip_lines = [f"━━━━━━━━━━━━━━━━━━━━━━"]
        tooltip_lines.append(f"🔷 AGENT {node}")
        tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")

        ntype = node_types.get(node) if node_types else None

        if ntype == "U":
            color = "#97c2fc"
            shape = "dot"
            tooltip_lines.append(f"📌 TYPE: USER")
            tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
            
            if node_str in users_initial:
                init = users_initial[node_str]
                tooltip_lines.append(f"📊 INITIAL STATE:")
                tooltip_lines.append(f"   • b (bias):       {init.b:.4f}")
                tooltip_lines.append(f"   • c (confidence): {init.c:.4f}")
                tooltip_lines.append(f"   • e (emotion):    {init.e:.4f}")
                tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
            
            if node_str in users_final:
                final = users_final[node_str]
                tooltip_lines.append(f"📊 FINAL STATE:")
                tooltip_lines.append(f"   • b (bias):       {final['b']:.4f}")
                tooltip_lines.append(f"   • c (confidence): {final['c']:.4f}")
                tooltip_lines.append(f"   • e (emotion):    {final['e']:.4f}")
                
                if node_str in users_initial:
                    init_b = users_initial[node_str].b
                    init_e = users_initial[node_str].e
                    delta_b = final['b'] - init_b
                    delta_e = final['e'] - init_e
                    tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
                    tooltip_lines.append(f"📈 CHANGES:")
                    tooltip_lines.append(f"   • Δb: {delta_b:+.4f}")
                    tooltip_lines.append(f"   • Δe: {delta_e:+.4f}")

        elif ntype == "R":
            color = "#ff6666"
            shape = "square"
            tooltip_lines.append(f"📌 TYPE: 🔴 RED AGENT (Threat Actor)")
            tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
            tooltip_lines.append(f"⚠️  Generates malicious content")

        elif ntype == "L":
            color = "#66ff66"
            shape = "triangle"
            tooltip_lines.append(f"📌 TYPE: 🟢 LLM AGENT")
            tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
            tooltip_lines.append(f"🤖 Language Model")

        else:
            color = "#cccccc"
            shape = "dot"
            tooltip_lines.append(f"📌 TYPE: UNKNOWN")

        tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
        sent_messages = [e for e in timeline if e["from"] == node]
        received_messages = [e for e in timeline if e["to"] == node]
        tooltip_lines.append(f"📤 SENT: {len(sent_messages)}")
        tooltip_lines.append(f"📥 RECEIVED: {len(received_messages)}")
        tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
        tooltip_lines.append(f"🔗 CONNECTIONS:")
        tooltip_lines.append(f"   • Outgoing: {G.out_degree(node)}")
        tooltip_lines.append(f"   • Incoming: {G.in_degree(node)}")

        net.add_node(
            node,
            label=str(node),
            color=color,
            shape=shape,
            title="\n".join(tooltip_lines),
            font={"size": 14}
        )

    # -------------------------
    # EDGES - все серые по умолчанию
    # -------------------------
    edge_id = 0
    edge_map = {}

    for u, v, data in G.edges(data=True):
        key = (u, v)
        weight = data.get("weight", 0.8)
        
        # tooltip для ребра
        tooltip_lines = [f"━━━━━━━━━━━━━━━━━━━━━━"]
        tooltip_lines.append(f"🔗 EDGE: {u} → {v}")
        tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
        tooltip_lines.append(f"📊 Вес связи: {weight:.3f}")

        if key in message_transmissions and message_transmissions[key]:
            msgs = message_transmissions[key]
            tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
            tooltip_lines.append(f"📨 ВСЕГО СООБЩЕНИЙ: {len(msgs)}")
            
            for i, msg in enumerate(msgs, 1):
                text = msg.get("text", "")
                cat = msg.get("category", "unknown")
                h_val = msg.get("h", 0)
                b_val = msg.get("b", 0)
                t_time = msg.get("t", 0)
                
                # Определяем опасность сообщения по h-value
                is_dangerous = h_val > 0.5
                
                if cat == "threat":
                    icon = "⚠️"
                    cat_name = "ОПАСНОЕ (threat)"
                    is_dangerous = True
                elif cat == "manipulative":
                    icon = "🎭"
                    cat_name = "ОПАСНОЕ (манип.)"
                    is_dangerous = True
                elif cat == "neutral":
                    icon = "💬"
                    cat_name = "НЕЙТРАЛЬНОЕ"
                    is_dangerous = False
                elif cat == "llm":
                    if is_dangerous:
                        icon = "⚠️🤖"
                        cat_name = "ОПАСНОЕ (LLM)"
                    else:
                        icon = "💬🤖"
                        cat_name = "НЕЙТРАЛЬНОЕ (LLM)"
                else:
                    icon = "📝"
                    cat_name = cat.upper()
                
                tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
                tooltip_lines.append(f"{icon} СООБЩЕНИЕ #{i} [{cat_name}] в t={t_time}")
                tooltip_lines.append(f"   • h (влияние): {h_val:.3f}")
                tooltip_lines.append(f"   • b (смещение): {b_val:.3f}")
                tooltip_lines.append(f"   • текст: \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
        else:
            tooltip_lines.append(f"━━━━━━━━━━━━━━━━━━━━━━")
            tooltip_lines.append(f"💤 Сообщений не передавалось")

        # Все ребра изначально серые
        net.add_edge(
            u,
            v,
            id=edge_id,
            color="#95a5a6",
            width=1,
            title="\n".join(tooltip_lines),
            arrows="to"
        )
        edge_map[key] = edge_id
        edge_id += 1

    # -------------------------
    # TIMELINE - группируем события по времени
    # -------------------------
    timeline_by_time = {}
    for e in timeline:
        t = e["t"]
        if t not in timeline_by_time:
            timeline_by_time[t] = []
        # Добавляем информацию об опасности для LLM сообщений
        e_with_danger = e.copy()
        if e.get("category") == "llm":
            e_with_danger["is_dangerous"] = e.get("h", 0) > 0.5
        timeline_by_time[t].append(e_with_danger)

    max_time = max(timeline_by_time.keys()) if timeline_by_time else 0
    timeline_json = json.dumps(timeline_by_time)

    html = net.generate_html()

    # -------------------------
    # JS С ПРАВИЛЬНОЙ АНИМАЦИЕЙ
    # -------------------------
    custom_js = f"""
<script>
// Данные по времени из Python
let timelineData = {timeline_json};
let currentTime = 0;
let animationInterval = null;
let edgeMap = {json.dumps({f"{k[0]},{k[1]}": v for k, v in edge_map.items()})};

// Функция сброса всех ребер в серый цвет
function resetAllEdges() {{
    let edges = network.body.data.edges;
    let allEdges = edges.get();
    
    for (let i = 0; i < allEdges.length; i++) {{
        let edge = allEdges[i];
        edges.update({{
            id: edge.id,
            color: "#95a5a6",
            width: 1,
            title: edge.originalTitle || edge.title
        }});
    }}
}}

// Функция подсветки конкретного ребра
function highlightEdge(fromNode, toNode, color, event) {{
    let edges = network.body.data.edges;
    let allEdges = edges.get();
    let edgeKey = fromNode + "," + toNode;
    let edgeId = edgeMap[edgeKey];
    
    if (edgeId !== undefined) {{
        let icon = "";
        let categoryText = "";
        
        if (event.category === "threat") {{
            icon = "⚠️";
            categoryText = "ОПАСНОЕ (threat)";
        }} else if (event.category === "manipulative") {{
            icon = "🎭";
            categoryText = "ОПАСНОЕ (манип.)";
        }} else if (event.category === "neutral") {{
            icon = "💬";
            categoryText = "НЕЙТРАЛЬНОЕ";
        }} else if (event.category === "llm") {{
            if (event.is_dangerous) {{
                icon = "⚠️🤖";
                categoryText = "ОПАСНОЕ (LLM)";
            }} else {{
                icon = "💬🤖";
                categoryText = "НЕЙТРАЛЬНОЕ (LLM)";
            }}
        }}
        
        let tooltip = "━━━━━━━━━━━━━━━━━━━━━━\\n";
        tooltip += icon + " АКТИВНОЕ СОБЫТИЕ в t=" + event.t + "\\n";
        tooltip += "━━━━━━━━━━━━━━━━━━━━━━\\n";
        tooltip += "📂 Тип: " + categoryText + "\\n";
        tooltip += "📊 h-value: " + event.h.toFixed(3) + "\\n";
        
        if (event.text) {{
            tooltip += "━━━━━━━━━━━━━━━━━━━━━━\\n";
            tooltip += "💬 ТЕКСТ:\\n";
            let text = event.text;
            if (text.length > 80) text = text.substring(0, 80) + "...";
            tooltip += "\\"" + text + "\\"\\n";
        }}
        
        edges.update({{
            id: edgeId,
            color: color,
            width: 4,
            title: tooltip
        }});
    }}
}}

// Обновление графа для конкретного времени
function updateByTime(time) {{
    resetAllEdges();
    
    let events = timelineData[time] || [];
    
    // Подсчет опасных и нейтральных сообщений
    let dangerousCount = 0;
    let neutralCount = 0;
    
    for (let i = 0; i < events.length; i++) {{
        let e = events[i];
        if (e.category === "threat" || e.category === "manipulative") {{
            dangerousCount++;
        }} else if (e.category === "llm" && e.is_dangerous) {{
            dangerousCount++;
        }} else if (e.category === "neutral" || (e.category === "llm" && !e.is_dangerous)) {{
            neutralCount++;
        }}
    }}
    
    document.getElementById("timeLabel").innerHTML = 
        "⏱ ВРЕМЯ: " + time + 
        " | 🔴 Опасных: " + dangerousCount +
        " | 🔵 Нейтральных: " + neutralCount;
    
    // Подсвечиваем каждое событие
    for (let i = 0; i < events.length; i++) {{
        let event = events[i];
        let color = "#3498db";  // голубой для нейтральных
        
        // Определяем цвет: красный для опасных, синий для нейтральных
        let isDangerous = false;
        
        if (event.category === "threat" || event.category === "manipulative") {{
            isDangerous = true;
        }} else if (event.category === "llm" && event.is_dangerous) {{
            isDangerous = true;
        }}
        
        if (isDangerous) {{
            color = "#e74c3c";  // КРАСНЫЙ для опасных
        }} else {{
            color = "#3498db";  // СИНИЙ для нейтральных
        }}
        
        highlightEdge(event.from, event.to, color, event);
    }}
}}

// Обработчик ползунка
function onTimeChange(value) {{
    currentTime = parseInt(value);
    updateByTime(currentTime);
    
    if (animationInterval) {{
        clearInterval(animationInterval);
        animationInterval = null;
        document.getElementById("playBtn").innerHTML = "▶ Play";
    }}
}}

// Автоматическое воспроизведение
function playAnimation() {{
    if (animationInterval) {{
        clearInterval(animationInterval);
        animationInterval = null;
        document.getElementById("playBtn").innerHTML = "▶ Play";
        return;
    }}
    
    document.getElementById("playBtn").innerHTML = "⏸ Pause";
    animationInterval = setInterval(function() {{
        if (currentTime >= {max_time}) {{
            clearInterval(animationInterval);
            animationInterval = null;
            document.getElementById("playBtn").innerHTML = "▶ Play";
            return;
        }}
        currentTime++;
        document.getElementById("timeSlider").value = currentTime;
        updateByTime(currentTime);
    }}, 800);
}}

// Сброс анимации
function resetAnimation() {{
    if (animationInterval) {{
        clearInterval(animationInterval);
        animationInterval = null;
        document.getElementById("playBtn").innerHTML = "▶ Play";
    }}
    currentTime = 0;
    document.getElementById("timeSlider").value = 0;
    updateByTime(0);
}}

// Сохраняем оригинальные заголовки при загрузке
network.on("stabilizationIterationsDone", function() {{
    let edges = network.body.data.edges;
    let allEdges = edges.get();
    for (let i = 0; i < allEdges.length; i++) {{
        let edge = allEdges[i];
        edge.originalTitle = edge.title;
        edges.update(edge);
    }}
    updateByTime(0);
}});
</script>

<!-- CONTROL PANEL -->
<div style="
position: fixed;
bottom: 20px;
left: 50%;
transform: translateX(-50%);
background: white;
padding: 15px 20px;
border-radius: 12px;
box-shadow: 0 0 15px rgba(0,0,0,0.3);
font-family: Arial, sans-serif;
z-index: 999;
">

<div style="text-align:center; margin-bottom:8px;">
<b>📊 ШКАЛА ВРЕМЕНИ</b>
</div>

<div style="display: flex; gap: 10px; align-items: center; justify-content: center;">
    <button id="playBtn" onclick="playAnimation()" style="padding: 5px 15px; cursor: pointer;">▶ Play</button>
    <button onclick="resetAnimation()" style="padding: 5px 15px; cursor: pointer;">⏮ Reset</button>
    <input type="range"
        id="timeSlider"
        min="0"
        max="{max_time}"
        value="0"
        onchange="onTimeChange(this.value)"
        style="width: 350px; cursor: pointer;"
    />
</div>

<div id="timeLabel" style="text-align:center; margin-top: 8px; font-size: 12px;">
⏱ ВРЕМЯ: 0
</div>

<div style="display: flex; gap: 20px; margin-top: 10px; font-size: 12px; justify-content: center;">
    <span style="color:#e74c3c;">🔴</span> Опасное сообщение
    <span style="color:#3498db;">🔵</span> Нейтральное сообщение
    <span style="color:#95a5a6;">⚪</span> Нет сообщений
</div>

<div style="text-align:center; margin-top: 8px; font-size: 10px; color: #666;">
💡 Наведи на узел → данные агента | Наведи на ребро → детали сообщений
</div>
</div>

<style>
.vis-tooltip {{
    background: rgba(0,0,0,0.92);
    color: #fff;
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 11px;
    font-family: 'Courier New', monospace;
    white-space: pre-line;
    max-width: 400px;
    line-height: 1.4;
}}
</style>
"""

    html = html.replace("</body>", custom_js + "</body>")

    with open("network_visualization_pro.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ Визуализация сохранена: network_visualization_pro.html")
 