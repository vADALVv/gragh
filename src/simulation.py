from __future__ import annotations

import math
import random
import os
import copy
import json
import networkx as nx
from dataclasses import dataclass
from typing import Dict, List


# =====================================================
# GLOBAL
# =====================================================

SEED = 42
random.seed(SEED)


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class Message:
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

neutral_messages: List[str] = []
threat_messages: List[str] = []
manipulative_messages: List[str] = []

_MESSAGES_LOADED = False


# =====================================================
# LOAD messages.txt
# =====================================================

def load_messages(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERROR] messages file not found: {path}")

    local_vars = {}

    with open(path, "r", encoding="utf-8") as f:
        exec(f.read(), {}, local_vars)

    required = ["neutral_messages", "threat_messages", "manipulative_messages"]

    for r in required:
        if r not in local_vars:
            raise ValueError(f"[ERROR] missing {r} in messages.txt")

    return (
        local_vars["neutral_messages"],
        local_vars["threat_messages"],
        local_vars["manipulative_messages"]
    )


def init_message_bank(path: str):
    global neutral_messages, threat_messages, manipulative_messages, _MESSAGES_LOADED

    neutral_messages, threat_messages, manipulative_messages = load_messages(path)
    _MESSAGES_LOADED = True


def _check_bank():
    if not _MESSAGES_LOADED:
        raise RuntimeError("Call init_message_bank(path) before simulation")


# =====================================================
# SERIALIZATION FIX (ВАЖНО)
# =====================================================

def serialize_users(users_state: Dict[int, UserState]):
    return {
        k: {
            "b": v.b,
            "c": v.c,
            "e": v.e
        }
        for k, v in users_state.items()
    }


# =====================================================
# MATH
# =====================================================

def sigmoid(x: float) -> float:
    x = max(-10, min(10, x))
    return 1 / (1 + math.exp(-x))


def kappa(b_i: float, b_m: float, alpha: float) -> float:
    return math.exp(-alpha * abs(b_m - b_i))


def affect(msg: Message) -> float:
    return msg.h


# =====================================================
# STATE UPDATE
# =====================================================

def update_user_state(state: UserState, msg: Message, rp: RepostParams):
    k = kappa(state.b, msg.b, rp.alpha)

    e_new = max(-2, min(2, state.e + affect(msg)))
    b_new = state.b + rp.beta * k * (msg.b - state.b)
    b_new = max(-1, min(1, b_new))

    return UserState(b_new, state.c, e_new), k


# =====================================================
# REPOST PROBABILITY
# =====================================================

def repost_probability(state: UserState, msg: Message, k: float, rel: float, rp: RepostParams):
    x = (
        rp.lambda0
        + rp.lambda1 * k
        + rp.lambda2 * state.e
        + rp.lambda3 * msg.h
        + rp.lambda4 * rel
    )
    return sigmoid(x)


# =====================================================
# MESSAGE GENERATION
# =====================================================

def generate_message(node_type: str, node_id: int, t: int):
    _check_bank()

    if node_type == "U":
        text = random.choice(neutral_messages)
        h = random.uniform(0.0, 0.3)
        category = "neutral"

    elif node_type == "R":
        text = random.choice(threat_messages + manipulative_messages)
        h = random.uniform(0.7, 1.0)
        category = "threat"

    elif node_type == "L":
        text = random.choice(neutral_messages + threat_messages + manipulative_messages)
        h = random.uniform(0.0, 1.0)
        category = "llm"

    else:
        return None

    return Message(
        text=text,
        b=random.uniform(-1, 1),
        h=h,
        src=node_id,
        t=t,
        category=category
    )


# =====================================================
# SIMULATION CORE
# =====================================================

def simulate_diffusion(
    G: nx.DiGraph,
    users: Dict[int, UserState],
    node_types: Dict[int, str],
    initial_messages=None,
    T_steps: int = 10,
    rp: RepostParams = RepostParams(),
    seed: int = 42,
    messages_path: str = r"C:\Users\Vlada\Desktop\llm_attaks\graph\data\messages.txt"
):

    random.seed(seed)

    init_message_bank(messages_path)

    users_state = {k: copy.deepcopy(v) for k, v in users.items()}

    active_queue = list(initial_messages) if initial_messages else []
    timeline = []
    seen = set()

    for t in range(T_steps):

        # генерация новых сообщений
        for node_id, ntype in node_types.items():
            msg = generate_message(ntype, node_id, t)
            active_queue.append((node_id, msg))

        next_queue = []

        for sender, msg in active_queue:

            if sender in users_state:
                state = users_state[sender]
                new_state, k = update_user_state(state, msg, rp)
                users_state[sender] = new_state
            else:
                k = 1.0

            for v in G.successors(sender):

                key = (v, msg.text)
                if key in seen:
                    continue

                rel = G[sender][v].get("weight", 1.0)

                p = repost_probability(users_state[v], msg, k, rel, rp)

                if random.random() < p:
                    seen.add(key)

                    next_queue.append((v, msg))

                    timeline.append({
                        "t": t,
                        "from": sender,
                        "to": v,
                        "text": msg.text,
                        "category": msg.category,
                        "h": msg.h,
                        "state_b": users_state[v].b,
                        "state_e": users_state[v].e
                    })

        active_queue = next_queue

    return {
        "users_final": serialize_users(users_state),
        "timeline": timeline
    }