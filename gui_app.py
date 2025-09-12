import os, time, requests, re, html
from flask import Flask, request, jsonify, render_template_string
from memory_manager import load_bootstrap_prompt

# -------- config from env (defaults chosen for snappy CPU use) --------
BASE  = os.getenv('JENNY_BASE',  'http://127.0.0.1:11435')
MODEL = os.getenv('JENNY_MODEL', 'fast')

OPTS = {
    "num_ctx":     int(os.getenv('JENNY_NUM_CTX', '512')),
    "num_predict": int(os.getenv('JENNY_NUM_PREDICT', '64')),
    "num_thread":  int(os.getenv('JENNY_THREADS', '4')),
    "temperature": float(os.getenv('JENNY_TEMP', '0.2')),
    "top_p":       float(os.getenv('JENNY_TOP_P', '0.9')),
    "seed":        int(os.getenv('JENNY_SEED', '42')),

    # ---- ONE CHANGE: anti-repetition defaults ----
    "repeat_penalty": float(os.getenv('JENNY_REPEAT_PENALTY', '1.22')),
    "repeat_last_n":  int(os.getenv('JENNY_REPEAT_LAST_N',  '192')),
}

print(f"[Jenny GUI] BASE={BASE} MODEL={MODEL} OPTS={OPTS}", flush=True)

def ask_local(user_text: str) -> str:
    msgs = [{"role": "user", "content": user_text}]
    r = requests.post(
        f"{BASE}/api/chat",
        json={"model": MODEL, "messages": msgs, "options": OPTS, "stream": False},
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "")

# Flask + HTML code unchanged (rest of file stays as in your original)
# ...
