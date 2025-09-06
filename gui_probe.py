import os, time, requests
from flask import Flask, request, jsonify

BASE  = os.getenv('JENNY_BASE',  'http://127.0.0.1:11435')
MODEL = os.getenv('JENNY_MODEL', 'fast')
OPTS  = {
    "num_ctx":    int(os.getenv('JENNY_NUM_CTX', '512')),
    "num_predict":int(os.getenv('JENNY_NUM_PREDICT', '64')),
    "num_thread": int(os.getenv('JENNY_THREADS', '4')),
}

def ask_local(text: str) -> str:
    sys_prompt = "You are Jenny. Be concise and warm."
    try:
        r = requests.post(f"{BASE}/api/chat", json={
            "model": MODEL,
            "messages": [
                {"role":"system","content":sys_prompt},
                {"role":"user","content":text}
            ],
            "options": OPTS,
            "stream": False
        }, timeout=60)
        if r.status_code == 404:
            raise RuntimeError("chat endpoint not available")
        r.raise_for_status()
        return r.json().get("message",{}).get("content","")
    except Exception:
        r = requests.post(f"{BASE}/api/generate", json={
            "model": MODEL,
            "prompt": f"{sys_prompt}\n\n{text}\n",
            "options": OPTS,
            "stream": False
        }, timeout=60)
        r.raise_for_status()
        return r.json().get("response","")

app = Flask(__name__)

@app.get("/api/ping")
def ping():
    t=time.time(); err=""
    try:
        v=requests.get(f"{BASE}/api/version", timeout=2)
        v.raise_for_status()
    except Exception as e:
        err=str(e)
    return jsonify({"ok": err=="", "rtt_ms": int((time.time()-t)*1000), "base": BASE, "model": MODEL, "error": err})

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": True, "reply": ""})
    try:
        reply = ask_local(text)
        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run("127.0.0.1", 7861, debug=False)
