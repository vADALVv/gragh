#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import re
import numpy as np
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    BitsAndBytesConfig,
)

from peft import PeftModel


# ==========================================================
# BLUE AGENT (OPTIMIZED FOR GPU)
# ==========================================================

class BlueAgent:

    def __init__(
        self,
        model_type="deberta",
        model_dir=None,
        max_length=4096,
        threshold=0.3,
        device="auto",
        load_in_4bit=True,
        batch_size=32,  # NEW: batch processing
    ):

        self.model_type = model_type.lower()
        self.max_length = max_length
        self.threshold = threshold
        self.load_in_4bit = load_in_4bit
        self.batch_size = batch_size  # NEW

        # FORCE GPU if available
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Print device info
        print(f"🔧 BlueAgent using device: {self.device.upper()}")
        if self.device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

        # history buffers (GLOBAL STATE)
        self.risk_history = []
        self.level_history = []
        
        # Cache for repeated texts (NEW)
        self.cache = {}

        # model config
        if self.model_type == "qwen":

            if model_dir is None:
                raise ValueError("model_dir is required for qwen model")

            self.base_model_path = os.path.join(
                model_dir, "models", "Qwen3-4B-Instruct-2507"
            )
            self.peft_model_path = os.path.join(
                model_dir, "lora_adapter"
            )
            self.model_class = AutoModelForTokenClassification

        elif self.model_type == "deberta":

            self.base_model_path = "microsoft/deberta-v3-base"
            self.peft_model_path = None
            self.model_class = AutoModelForTokenClassification

        else:
            raise ValueError(f"Unknown model_type: {self.model_type}")

        self._load_model()

    # ======================================================
    # LOAD MODEL
    # ======================================================

    def _load_model(self):

        print(f"📥 Loading tokenizer from {self.base_model_path}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_path,
            trust_remote_code=True
        )
        
        # Set padding token if not set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        model_kwargs = {
            "num_labels": 2,
            "trust_remote_code": True
        }

        # Only use 4-bit quantization on GPU
        if self.load_in_4bit and self.device == "cuda":
            print("🔧 Loading model with 4-bit quantization...")
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            model_kwargs["device_map"] = "auto"
        else:
            print("🔧 Loading model in full precision...")

        print(f"📥 Loading model from {self.base_model_path}...")
        base_model = self.model_class.from_pretrained(
            self.base_model_path,
            **model_kwargs
        )

        if self.model_type == "qwen" and self.peft_model_path:
            print("📥 Loading PEFT adapter...")
            self.model = PeftModel.from_pretrained(
                base_model,
                self.peft_model_path
            )
        else:
            self.model = base_model

        # Move to device if not using device_map
        if not (self.load_in_4bit and self.device == "cuda"):
            print(f"📥 Moving model to {self.device}...")
            self.model = self.model.to(self.device)

        self.model.eval()
        print("✅ Model loaded successfully!")

    # ======================================================
    # LABEL
    # ======================================================

    def _risk_label(self, score: float) -> str:
        if score < 0.2:
            return "SAFE"
        elif score < 0.45:
            return "LOW"
        elif score < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"

    # ======================================================
    # ANALYZE BATCH OF TEXTS (FASTER ON GPU)
    # ======================================================

    def analyze_batch(self, texts):
        """
        Analyze multiple texts in batch for better GPU utilization
        """
        results = []
        texts_to_process = []
        indices_to_process = []
        
        # Check cache first
        for i, text in enumerate(texts):
            if text in self.cache:
                results.append(self.cache[text])
            else:
                texts_to_process.append(text)
                indices_to_process.append(i)
        
        if not texts_to_process:
            return results
        
        system_prompt = (
            "Определи опасные фрагменты: угрозы, насилие, оружие, "
            "наркотики, мошенничество, манипуляции, экстремизм."
        )
        
        # Prepare batch
        batch_inputs = []
        for text in texts_to_process:
            try:
                full_input = self.tokenizer.apply_chat_template(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text},
                    ],
                    tokenize=False,
                    add_generation_prompt=False,
                )
            except Exception:
                full_input = f"{system_prompt}\n\nUSER:\n{text}"
            batch_inputs.append(full_input)
        
        # Tokenize batch
        enc = self.tokenizer(
            batch_inputs,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
            padding=True,  # Pad to max length in batch
        )
        
        # Move to device
        enc = {k: v.to(self.device) for k, v in enc.items()}
        
        # Process batch
        with torch.no_grad():
            outputs = self.model(**enc)
            probs_batch = torch.sigmoid(outputs.logits[:, :, 1]).cpu().numpy()
        
        # Process each text in batch
        for idx, (text, probs) in enumerate(zip(texts_to_process, probs_batch)):
            # Get offsets for this text
            enc_plain = self.tokenizer(
                batch_inputs[idx],
                return_offsets_mapping=True,
                truncation=True,
                max_length=self.max_length,
                padding=False,
            )
            offsets = enc_plain["offset_mapping"]
            
            start_user = batch_inputs[idx].find(text)
            if start_user == -1:
                start_user = 0
            
            suspicious = []
            
            for w in re.finditer(r"\S+", text):
                ws, we = w.start(), w.end()
                max_p = 0.0
                
                for i, p in enumerate(probs):
                    if i >= len(offsets):
                        break
                    
                    ts, te = offsets[i]
                    rs = ts - start_user
                    re_ = te - start_user
                    
                    if max(ws, rs) < min(we, re_):
                        max_p = max(max_p, float(p))
                
                if max_p >= self.threshold:
                    suspicious.append((text[ws:we], round(max_p, 3)))
            
            scores = [s for _, s in suspicious]
            
            if not scores:
                risk_score = 0.0
            else:
                scores = np.array(scores)
                weights = np.exp(scores / 2.0)
                weights = weights / np.sum(weights)
                risk_score = float(np.sum(weights * scores))
                risk_score = float(np.clip(risk_score, 0, 1))
            
            result = {
                "RiskScore": round(risk_score, 4),
                "Level": self._risk_label(risk_score),
                "sus_words": suspicious
            }
            
            # Cache result
            self.cache[text] = result
            results.append(result)
        
        # Reorder results to match original order
        final_results = [None] * len(texts)
        cache_idx = 0
        for i, text in enumerate(texts):
            if text in self.cache:
                final_results[i] = self.cache[text]
            else:
                final_results[i] = results[cache_idx]
                cache_idx += 1
        
        return final_results

    # ======================================================
    # ANALYZE SINGLE TEXT
    # ======================================================

    def analyze(self, messages):
        """
        Analyze single text (uses batch method internally)
        """
        if isinstance(messages, list):
            text = " ".join(messages)
        else:
            text = messages
        
        # Use cache
        if text in self.cache:
            return self.cache[text]
        
        # Process single text
        result = self.analyze_batch([text])[0]
        return result

    # ======================================================
    # STREAM PROCESSING (WITH BATCHING)
    # ======================================================

    def process_event(self, text: str):
        """
        Process single event (used in simulation)
        """
        result = self.analyze(text)
        
        self.risk_history.append(result["RiskScore"])
        self.level_history.append(result["Level"])
        
        return result["RiskScore"], result["Level"]
    
    def process_batch(self, texts):
        """
        Process batch of events (more efficient)
        """
        results = self.analyze_batch(texts)
        
        for result in results:
            self.risk_history.append(result["RiskScore"])
            self.level_history.append(result["Level"])
        
        return [(r["RiskScore"], r["Level"]) for r in results]

    # ======================================================
    # GLOBAL SUMMARY
    # ======================================================

    def global_summary(self):

        if not self.risk_history:
            return {
                "global_risk_score": 0.0,
                "global_risk_level": "SAFE"
            }

        score = float(np.mean(self.risk_history))

        if score < 0.2:
            level = "SAFE"
        elif score < 0.45:
            level = "LOW"
        elif score < 0.7:
            level = "MEDIUM"
        else:
            level = "HIGH"

        return {
            "global_risk_score": round(score, 4),
            "global_risk_level": level
        }
    
    def clear_cache(self):
        """Clear analysis cache"""
        self.cache = {}
        print("🗑️ Cache cleared")
    
    def get_stats(self):
        """Get agent statistics"""
        return {
            "total_analyzed": len(self.risk_history),
            "cache_size": len(self.cache),
            "avg_risk": np.mean(self.risk_history) if self.risk_history else 0,
            "device": self.device,
            "model_type": self.model_type
        }