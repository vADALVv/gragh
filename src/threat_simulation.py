from __future__ import annotations

import math
import random
import os
from dataclasses import dataclass
from typing import List


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


# =====================================================
# INIT BANK
# =====================================================

def init_message_bank(path: str):
    global neutral_messages, threat_messages, manipulative_messages, _MESSAGES_LOADED

    neutral_messages, threat_messages, manipulative_messages = load_messages(path)
    _MESSAGES_LOADED = True


def _check_bank():
    if not _MESSAGES_LOADED:
        raise RuntimeError("Call init_message_bank(path) before simulation")


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
# MESSAGE GENERATION (FIXED LOGIC)
# =====================================================

def generate_message(node_type: str, node_id: int, t: int):
    _check_bank()

    # -------------------------
    # USER
    # -------------------------
    if node_type == "U":
        return Message(
            text=random.choice(neutral_messages),
            b=random.uniform(-1, 1),
            h=random.uniform(0.0, 0.3),
            src=node_id,
            t=t,
            category="neutral"
        )

    # -------------------------
    # THREAT ACTOR
    # -------------------------
    if node_type == "R":
        if random.random() < 0.5:
            text = random.choice(threat_messages)
            category = "threat"
            h = random.uniform(0.7, 1.0)
        else:
            text = random.choice(manipulative_messages)
            category = "manipulative"
            h = random.uniform(0.6, 0.9)

        return Message(
            text=text,
            b=random.uniform(-1, 1),
            h=h,
            src=node_id,
            t=t,
            category=category
        )

    # -------------------------
    # LLM NODE
    # -------------------------
    if node_type == "L":
        r = random.random()

        if r < 0.6:
            text = random.choice(neutral_messages)
            category = "llm_neutral"
            h = random.uniform(0.0, 0.3)

        elif r < 0.85:
            text = random.choice(threat_messages)
            category = "llm_threat"
            h = random.uniform(0.7, 1.0)

        else:
            text = random.choice(manipulative_messages)
            category = "llm_manipulative"
            h = random.uniform(0.5, 0.9)

        return Message(
            text=text,
            b=random.uniform(-1, 1),
            h=h,
            src=node_id,
            t=t,
            category=category
        )

    return None