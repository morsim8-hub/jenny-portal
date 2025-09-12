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

    # ---- ONE CHANGE: anti-repetition controls (safe defaults) ----
    "repeat_penalty": float(os.getenv('JENNY_REPEAT_PENALTY', '1.22')),
    "repeat_last_n":  int(os.getenv('JENNY_REPEAT_LAST_N',  '192')),
}

print(f"[Jenny GUI] BASE={BASE} MODEL={MODEL} OPTS={OPTS}", flush=True)

# -------- single, local caller (chat first, generate as fallback) -----
def ask_local(user_text: str) -> str:
    # Always ignore memory_manager for now (test mode)
    msgs = [
        {"role": "user", "content": user_text}
    ]

    # Force the model to answer with its baked-in system (Modelfile)
    r = requests.post(
        f"{BASE}/api/chat",
        json={
            "model": MODEL,
            "messages": msgs,
            "options": OPTS,
            "stream": False,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("message", {}).get("content", "")

# ----------------------------- Flask ---------------------------------
APP = Flask(__name__)

PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Jenny Prime — Local GUI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    :root{--bg:#0b0c10;--card:#0f1115;--fg:#e8e8e8;--mut:#aaa;--ok:#3fb950;--bad:#e5534b;--acc:#2b7a78;--br:#222}
    *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}
    header{padding:10px 12px;background:#111;border-bottom:1px solid var(--br);display:flex;gap:10px;align-items:center;flex-wrap:wrap}
    .pill{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border:1px solid var(--br);border-radius:999px;background:var(--card);font-size:13px}
    .dot{width:10px;height:10px;border-radius:50%;background:#777}.ok{background:var(--ok)}.bad{background:var(--bad)}
    main{max-width:900px;margin:0 auto;padding:14px}
    #log{height:62vh;overflow:auto;border:1px solid var(--br);border-radius:12px;padding:12px;background:var(--card)}
    .u,.a{margin:10px 0;white-space:pre-wrap}.u{color:#9fd3c7}.a{color:#f8f8f2}.ts{color:var(--mut);font-size:11px;margin-left:6px}
    form{display:flex;gap:10px;margin-top:12px;align-items:flex-start}
    textarea{flex:1;min-height:54px;max-height:160px;resize:vertical;border-radius:12px;border:1px solid #333;background:var(--card);color:var(--fg);padding:10px}
    button{padding:10px 14px;border:none;border-radius:12px;background:var(--acc);color:#fff;cursor:pointer}
    button:disabled{opacity:.6;cursor:not-allowed}
  </style>
</head>
<body>
<header>
  <span class="pill"><span id="dot" class="dot"></span><span id="stat">checking…</span></span>
  <span class="pill">model: <strong id="model">—</strong></span>
  <span class="pill" style="color:#cfc">Enter = send · Shift+Enter = newline</span>
</header>
<main>
  <div id="log"></div>
  <form id="f">
    <textarea id="q" placeholder="Type to Jenny…" autofocus></textarea>
    <button id="send">Send</button>
  </form>
</main>
<script>
document.addEventListener('DOMContentLoaded', ()=>{
  const log   = document.getElementById('log');
  const q     = document.getElementById('q');
  const btn   = document.getElementById('send');
  const form  = document.getElementById('f');
  const dot   = document.getElementById('dot');
  const stat  = document.getElementById('stat');
  const model = document.getElementById('model');

  function ts(){ return new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}); }
  function add(role,text){
    const div=document.createElement('div'); div.className=(role==='user'?'u':'a');
    div.innerHTML = `<strong>${role==='user'?'You':'Jenny'}:</strong> ${text} <span class="ts">${ts()}</span>`;
    log.appendChild(div); log.scrollTop = log.scrollHeight;
  }

  async function ping(){
    try{
      const r = await fetch('/api/ping'); const j = await r.json();
      if (model) model.textContent = j.model || '—';
      if (stat)  stat.textContent  = j.ok ? `online ${j.rtt_ms} ms` : (j.error||'offline');
      if (dot)  { dot.classList.toggle('ok', !!j.ok); dot.classList.toggle('bad', !j.ok); }
    }catch(e){
      if (stat) stat.textContent='offline'; if (dot){ dot.classList.remove('ok'); dot.classList.add('bad'); }
    }
  }
  setInterval(ping, 8000); ping();

  form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const text = (q.value||'').trim(); if(!text) return;
    add('user', text); btn.disabled = true;
    try{
      const r = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text})});
      const raw = await r.text();
      let j=null; try{ j=JSON.parse(raw); }catch{ add('assistant','⚠️ server returned non-JSON:\\n'+raw.slice(0,400)); return; }
      if(!j.ok){ add('assistant','⚠️ '+(j.error||'unknown error')); return; }
      add('assistant', j.reply || '(no reply)');
    }catch(err){ add('assistant','⚠️ '+err); }
    finally{ btn.disabled=false; q.value=''; q.focus(); }
  });

  q.addEventListener('keydown', (e)=>{
    if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); form.requestSubmit(); }
  });
});
</script>
</body></html>
"""

@APP.get("/")
def home():
    return render_template_string(PAGE)

@APP.get("/api/ping")
def api_ping():
    t0=time.time(); err=""; ok=False
    try:
        v=requests.get(f"{BASE}/api/version", timeout=2)
        v.raise_for_status(); ok=True
    except Exception as e:
        err=str(e)
    return jsonify({"ok": ok, "rtt_ms": int((time.time()-t0)*1000), "base": BASE, "model": MODEL, "error": err})

@APP.post("/api/chat")
def api_chat():
    t0=time.time()
    try:
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"ok": True, "reply": ""})
        reply = ask_local(text)
        return jsonify({"ok": True, "reply": reply, "ms": int((time.time()-t0)*1000)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    APP.run(host="127.0.0.1", port=7860, debug=False, use_reloader=False, threaded=True)

# --- health endpoint (liveness probe) ---
@APP.route("/health", methods=["GET"])
def health():
    import time
    try:
        from chat_loop import MODEL as CHAT_MODEL
    except Exception:
        CHAT_MODEL = "unknown"
    return {"ok": True, "model": CHAT_MODEL, "ts": time.time()}
::contentReference[oaicite:0]{index=0}
