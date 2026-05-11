# llm_agents.py
import json
import re
from transformers import pipeline


class LLMAgentManager:

    def __init__(self):

        print("[LLM] loading model...")

        self.generator = pipeline(
            "text-generation",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            device_map="auto"
        )

        print("[LLM] model loaded")

        self.histories = {}
        self.beliefs = {}

    # =========================
    # INIT NODE
    # =========================

    def init_agent(self, node_id, persona="neutral", belief=0.0):

        self.histories[node_id] = {
            "persona": persona,
            "messages": []
        }

        self.beliefs[node_id] = belief

    def get_belief(self, node_id):
        return self.beliefs.get(node_id, 0.0)

    # =========================
    # MEMORY UPDATE
    # =========================

    def receive_message(self, node_id, text):

        if node_id not in self.histories:
            return

        self.histories[node_id]["messages"].append(text)

        # ограничиваем память
        self.histories[node_id]["messages"] = self.histories[node_id]["messages"][-10:]

    # =========================
    # GENERATION
    # =========================

    def generate_message(self, node_id, timestep):

        if node_id not in self.histories:
            return None

        memory = self.histories[node_id]

        history_text = "\n".join(memory["messages"][-5:])

        prompt = f"""
You are a social media agent.

Persona: {memory['persona']}

History:
{history_text}

Return JSON:
{{
  "message": "...",
  "h": 0.0,
  "category": "neutral | manipulative | threat"
}}

Only JSON.
"""

        out = self.generator(
            prompt,
            max_new_tokens=120,
            temperature=0.8,
            do_sample=True
        )

        text = out[0]["generated_text"]

        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            return {
                "message": "default message",
                "h": 0.2,
                "category": "neutral"
            }

        try:
            data = json.loads(match.group())
        except:
            data = {
                "message": "fallback message",
                "h": 0.2,
                "category": "neutral"
            }

        # sanitize
        data["h"] = float(data.get("h", 0.2))
        data["h"] = max(0.0, min(1.0, data["h"]))

        if "message" not in data:
            data["message"] = "empty"

        if "category" not in data:
            data["category"] = "neutral"

        # save memory
        self.histories[node_id]["messages"].append(data["message"])

        return data