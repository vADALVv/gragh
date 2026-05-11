from __future__ import annotations

import math
import random
import copy
from dataclasses import dataclass
from typing import Dict, Optional, List, Set, Tuple
from collections import defaultdict
import networkx as nx


# =====================================================
# MODELS
# =====================================================

@dataclass
class Message:
    msg_id: int
    text: str
    b: float
    h: float
    src: int
    t: int
    category: str


@dataclass
class UserState:
    b: float
    c: float
    e: float


@dataclass
class RepostParams:
    lambda0: float = -2.0
    lambda1: float = 4.0
    lambda2: float = 2.0
    lambda3: float = 2.0
    lambda4: float = 1.0
    alpha: float = 3.0
    beta: float = 0.2


# =====================================================
# MESSAGE BANK
# =====================================================

neutral_messages = []
threat_messages = []
manipulative_messages = []

_msg_counter = 0


def init_message_bank(path: str):
    import json
    global neutral_messages, threat_messages, manipulative_messages

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    neutral_messages.clear()
    threat_messages.clear()
    manipulative_messages.clear()

    for item in data:
        msg = {
            "text": item["text"],
            "b": float(item["b"]),
            "h": float(item["h"])
        }

        t = item.get("type", "neutral")

        if t == "neutral":
            neutral_messages.append(msg)
        elif t == "threat":
            threat_messages.append(msg)
        else:
            manipulative_messages.append(msg)


# =====================================================
# MATH
# =====================================================

def sigmoid(x: float):
    return 1 / (1 + math.exp(-max(-10, min(10, x))))


def kappa(b_i, b_m, alpha):
    return math.exp(-alpha * abs(b_m - b_i))


# =====================================================
# STATE UPDATE
# =====================================================

def update_user(state: UserState, msg: Message, rp: RepostParams):

    k = kappa(state.b, msg.b, rp.alpha)

    # эмоции — без насыщения в 2.0 (это ломало динамику)
    e_new = state.e * 0.97 + msg.h * 0.35
    e_new = max(-3, min(3, e_new))

    # belief update
    b_new = state.b + state.c * rp.beta * k * (msg.b - state.b)
    b_new = max(-1, min(1, b_new))

    # learning rate НЕ должен быстро “умирать”
    c_new = state.c + 0.003 * (k - 0.5)
    c_new = max(0.05, min(1.0, c_new))

    return UserState(b_new, c_new, e_new), k


# =====================================================
# MESSAGE GENERATION
# =====================================================

def generate(node_type: str, node_id: int, t: int) -> Optional[Message]:
    global _msg_counter

    pool = (
        neutral_messages if node_type == "U"
        else threat_messages if node_type == "R"
        else neutral_messages + threat_messages + manipulative_messages
    )

    if not pool:
        return None

    m = random.choice(pool)

    if m in threat_messages:
        cat = "threat"
    elif m in manipulative_messages:
        cat = "manipulative"
    else:
        cat = "neutral"

    msg = Message(
        msg_id=_msg_counter,
        text=m["text"],
        b=m["b"],
        h=m["h"],
        src=node_id,
        t=t,
        category=cat
    )

    _msg_counter += 1
    return msg


# =====================================================
# SIMULATION (FIXED EPIDEMIC MODEL)
# =====================================================
def simulate_diffusion(
    G: nx.DiGraph,
    users: Dict[int, UserState],
    node_types: Dict[int, str],
    T_steps: int = 10,
    rp: RepostParams = RepostParams(),
    seed: int = 42,
    messages_path: Optional[str] = None
):

    random.seed(seed)

    if messages_path:
        init_message_bank(messages_path)

    # копия состояния
    state = copy.deepcopy(users)

    timeline = []
    history = []

    # msg_id -> заражённые узлы
    infected: Dict[int, Set[int]] = defaultdict(set)

    # 🔥 ВАЖНО: теперь фронтир = (node, message, age)
    frontier: List[Tuple[int, Message, int]] = []

    global _msg_counter
    _msg_counter = 0

    # initial snapshot
    history.append({k: v.__dict__ for k, v in state.items()})

    # =====================================================
    # INITIAL SEED
    # =====================================================
    for node_id, ntype in node_types.items():
        msg = generate(ntype, node_id, 0)
        if msg:
            frontier.append((node_id, msg, 0))
            infected[msg.msg_id].add(node_id)

    # =====================================================
    # MAIN LOOP
    # =====================================================
    for t in range(T_steps):

        new_frontier: List[Tuple[int, Message, int]] = []

        # лёгкая динамика эмоций (чтобы система не замерла)
        for uid in state:
            state[uid].e *= 0.98

        # =================================================
        # diffusion step
        # =================================================
        for sender, msg, age in frontier:

            sender_state = state[sender]

            for receiver in G.successors(sender):

                if receiver in infected[msg.msg_id]:
                    continue

                rel = G[sender][receiver].get("weight", 1.0)

                k_val = kappa(state[receiver].b, msg.b, rp.alpha)

                viral_boost = 0.6 if msg.category in ("threat", "manipulative") else 0.0

                p = sigmoid(
                    rp.lambda0 +
                    rp.lambda1 * k_val +
                    rp.lambda2 * state[receiver].e +
                    rp.lambda3 * msg.h +
                    rp.lambda4 * rel +
                    viral_boost
                )

                # мягкое затухание, но НЕ убийство цепочки
                p *= (0.99 ** age)

                if random.random() < p:

                    # обновление состояния
                    state[receiver], _ = update_user(state[receiver], msg, rp)

                    infected[msg.msg_id].add(receiver)

                    # 🔥 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ:
                    # receiver становится новым источником распространения
                    new_frontier.append((receiver, msg, 0))

                    timeline.append({
                        "t": t,
                        "from": sender,
                        "to": receiver,
                        "msg_id": msg.msg_id,
                        "text": msg.text,
                        "category": msg.category,
                        "b": msg.b,
                        "h": msg.h,
                        "state_b": state[receiver].b,
                        "state_c": state[receiver].c,
                        "state_e": state[receiver].e
                    })

        # =================================================
        # если активность упала → НЕ останавливаем систему
        # добавляем новые источники (важно для устойчивости)
        # =================================================
        if not new_frontier:
            for node_id, ntype in node_types.items():
                if random.random() < 0.3:
                    msg = generate(ntype, node_id, t)
                    if msg:
                        new_frontier.append((node_id, msg, 0))
                        infected[msg.msg_id].add(node_id)

        frontier = new_frontier

        # snapshot ВСЕГДА
        history.append({k: v.__dict__ for k, v in state.items()})

    return {
        "users_final": {k: v.__dict__ for k, v in state.items()},
        "timeline": timeline,
        "states_history": history,
        "total_messages": _msg_counter
    }