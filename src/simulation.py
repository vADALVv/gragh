from __future__ import annotations

import math
import random
import copy
import json
import networkx as nx

from dataclasses import dataclass
from typing import Dict, Optional, List, Set, Tuple
from collections import defaultdict


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
    dst: Optional[int]
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

_MESSAGES_LOADED = False


def load_messages_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    neutral, threat, manipulative = [], [], []

    for item in data:
        msg = {
            "text": item["text"],
            "b": float(item["b"]),
            "h": float(item["h"])
        }

        t = item.get("type", "neutral")

        if t == "neutral":
            neutral.append(msg)
        elif t == "threat":
            threat.append(msg)
        else:
            manipulative.append(msg)

    return neutral, threat, manipulative


def init_message_bank(path: str):
    global neutral_messages, threat_messages, manipulative_messages, _MESSAGES_LOADED
    neutral_messages, threat_messages, manipulative_messages = load_messages_json(path)
    _MESSAGES_LOADED = True
    print(f"✅ Message bank loaded: {len(neutral_messages)} neutral, {len(threat_messages)} threat, {len(manipulative_messages)} manipulative")


def _check_bank():
    if not _MESSAGES_LOADED:
        raise RuntimeError("Call init_message_bank(path)")


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

def update_user_state(state: UserState, msg: Message, rp: RepostParams) -> Tuple[UserState, float]:
    k = kappa(state.b, msg.b, rp.alpha)

    e_new = max(-2, min(2, state.e + msg.h))

    b_new = state.b + state.c * rp.beta * k * (msg.b - state.b)
    b_new = max(-1, min(1, b_new))

    return UserState(b_new, state.c, e_new), k


# =====================================================
# PROBABILITY
# =====================================================

def repost_probability(state: UserState, msg: Message, k: float, rel: float, rp: RepostParams) -> float:
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

_msg_counter = 0


def generate_message(node_type: str, node_id: int, t: int) -> Optional[Message]:
    global _msg_counter
    _check_bank()

    if node_type == "U":  # USER - только нейтральные сообщения
        if not neutral_messages:
            return None
        msg = random.choice(neutral_messages)
        m = Message(
            msg_id=_msg_counter,
            text=msg["text"],
            b=msg["b"],
            h=msg["h"],
            src=node_id,
            dst=None,
            t=t,
            category="neutral"
        )
        _msg_counter += 1
        return m

    elif node_type == "R":  # RED AGENT - только угрозы и манипуляции
        all_threats = threat_messages + manipulative_messages
        if not all_threats:
            return None
        msg = random.choice(all_threats)
        # Определяем категорию
        if msg in threat_messages:
            category = "threat"
        else:
            category = "manipulative"
        m = Message(
            msg_id=_msg_counter,
            text=msg["text"],
            b=msg["b"],
            h=msg["h"],
            src=node_id,
            dst=None,
            t=t,
            category=category
        )
        _msg_counter += 1
        return m
    
    elif node_type == "L":  # LLM AGENT - любые сообщения
        msg_type = random.choice(["neutral", "threat", "manipulative"])
        if msg_type == "neutral" and neutral_messages:
            msg = random.choice(neutral_messages)
            category = "neutral"
        elif msg_type == "threat" and threat_messages:
            msg = random.choice(threat_messages)
            category = "threat"
        elif manipulative_messages:
            msg = random.choice(manipulative_messages)
            category = "manipulative"
        else:
            return None
        
        m = Message(
            msg_id=_msg_counter,
            text=msg["text"],
            b=msg["b"],
            h=msg["h"],
            src=node_id,
            dst=None,
            t=t,
            category=category
        )
        _msg_counter += 1
        return m

    return None


# =====================================================
# SIMULATION
# =====================================================

def simulate_diffusion(
    G: nx.DiGraph,
    users: Dict[int, UserState],
    node_types: Dict[int, str],
    T_steps: int = 10,
    rp: RepostParams = RepostParams(),
    seed: int = 42,
    messages_path: Optional[str] = None
) -> Dict:

    random.seed(seed)

    if messages_path:
        init_message_bank(messages_path)

    # Копируем состояния пользователей
    users_state = {k: copy.deepcopy(v) for k, v in users.items()}
    timeline = []
    
    # Сохраняем состояния узлов на каждом временном шаге
    states_history = []  # Список словарей {node_id: {b, c, e}} для каждого времени
    
    # Сохраняем начальное состояние (t = 0)
    initial_states = {
        str(k): {"b": v.b, "c": v.c, "e": v.e}
        for k, v in users_state.items()
    }
    states_history.append(initial_states)
    
    # Отслеживаем, какие сообщения получил каждый пользователь
    message_spread: Dict[int, Set[int]] = defaultdict(set)
    
    # Отслеживаем, какие сообщения отправил каждый пользователь
    user_messages: Dict[int, List[Tuple[Message, int]]] = defaultdict(list)

    # Очередь активных сообщений: (sender, message, age, path)
    active_queue: List[Tuple[int, Message, int, List[int]]] = []

    # =====================================================
    # INITIAL SEED - начальные сообщения в момент t=0
    # =====================================================
    print("🌱 Generating initial messages...")
    for node_id, ntype in node_types.items():
        msg = generate_message(ntype, node_id, 0)
        if msg:
            active_queue.append((node_id, msg, 0, [node_id]))
            message_spread[msg.msg_id].add(node_id)
            user_messages[node_id].append((msg, 0))
    
    print(f"📨 Initial active messages: {len(active_queue)}")

    # =====================================================
    # MAIN LOOP
    # =====================================================
    for t in range(T_steps):
        print(f"\n⏰ Step {t}/{T_steps-1}, Active queue: {len(active_queue)}")
        
        # Генерируем новые сообщения от всех узлов в текущий момент времени
        new_messages = []
        for node_id, ntype in node_types.items():
            # Красные агенты всегда генерируют сообщения
            if ntype == "R":
                msg = generate_message("R", node_id, t)
                if msg:
                    new_messages.append((node_id, msg))
                    message_spread[msg.msg_id].add(node_id)
                    user_messages[node_id].append((msg, t))
            
            # Обычные пользователи иногда генерируют сообщения
            elif ntype == "U":
                if random.random() < 0.3:  # 30% шанс создать сообщение
                    msg = generate_message("U", node_id, t)
                    if msg:
                        new_messages.append((node_id, msg))
                        message_spread[msg.msg_id].add(node_id)
                        user_messages[node_id].append((msg, t))
            
            # LLM агенты генерируют сообщения с средней вероятностью
            elif ntype == "L":
                if random.random() < 0.4:  # 40% шанс
                    msg = generate_message("L", node_id, t)
                    if msg:
                        new_messages.append((node_id, msg))
                        message_spread[msg.msg_id].add(node_id)
                        user_messages[node_id].append((msg, t))
        
        # Добавляем новые сообщения в очередь
        for sender, msg in new_messages:
            active_queue.append((sender, msg, 0, [sender]))
        
        # Обрабатываем текущую очередь
        next_queue = []
        
        for sender, msg, age, path in active_queue:
            
            # Пропускаем слишком старые сообщения
            if age > 5:
                continue
            
            # Обновляем состояние отправителя
            if sender in users_state:
                state, k = update_user_state(users_state[sender], msg, rp)
                users_state[sender] = state
            else:
                k = 1.0
            
            # Затухание со временем
            decay = 0.85 ** age
            
            # Для каждого получателя
            for receiver in G.successors(sender):
                
                # Проверяем, не получал ли уже этот пользователь данное сообщение
                if receiver in message_spread[msg.msg_id]:
                    continue
                
                # Получаем вес ребра (сила связи)
                rel = G[sender][receiver].get("weight", 1.0)
                
                # Вычисляем вероятность репоста
                p = repost_probability(users_state[receiver], msg, k, rel, rp)
                p *= decay
                
                # Репост
                if random.random() < p:
                    # Обновляем состояние получателя
                    if receiver in users_state:
                        state_rec, _ = update_user_state(users_state[receiver], msg, rp)
                        users_state[receiver] = state_rec
                    
                    # Отмечаем, что сообщение получено
                    message_spread[msg.msg_id].add(receiver)
                    
                    # Добавляем в следующую очередь для дальнейшего распространения
                    new_path = path + [receiver]
                    next_queue.append((receiver, msg, age + 1, new_path))
                    
                    # Записываем событие в таймлайн
                    timeline.append({
                        "t": t,
                        "from": sender,
                        "to": receiver,
                        "msg_id": msg.msg_id,
                        "text": msg.text,
                        "b": msg.b,
                        "h": msg.h,
                        "category": msg.category,
                        "event": "repost",
                        "state_b": users_state[receiver].b,  # Сохраняем состояние получателя
                        "state_c": users_state[receiver].c,
                        "state_e": users_state[receiver].e
                    })
        
        # Обновляем очередь для следующего шага
        active_queue = next_queue
        
        # Сохраняем состояние всех узлов после текущего шага (t+1)
        current_states = {
            str(k): {"b": v.b, "c": v.c, "e": v.e}
            for k, v in users_state.items()
        }
        states_history.append(current_states)
        
        # Останавливаем, если больше нет активных сообщений
        if not active_queue and not new_messages:
            print(f"\n✅ No more active messages at t={t}, stopping simulation")
            break

    print(f"\n📊 Simulation complete!")
    print(f"   Total timeline events: {len(timeline)}")
    print(f"   Total messages generated: {_msg_counter}")
    print(f"   Final users: {len(users_state)}")
    print(f"   States history snapshots: {len(states_history)}")
    
    # Возвращаем результаты
    return {
        "users_final": {k: v.__dict__ for k, v in users_state.items()},
        "timeline": timeline,
        "node_types": node_types,
        "states_history": states_history,
        "total_messages": _msg_counter
    }