# [F012] gui_app.py — Jenny GUI (file upload + URL fetch + voice + heartbeat + timestamps + Enter-to-send)
import datetime, time, re, html, requests
from flask import Flask, request, jsonify, render_template_string
from chat_loop import ask, MODEL as CHAT_MODEL, BASE as CHAT_BASE

APP = Flask(__name__)

# ---- server-side small fence to prevent echoes/dupes ----
_state = {"last_user": None, "t_user": 0.0, "last_reply": None}

def _strip_html(t: str) -> str:
    t = re.sub(r"<[^>]+>", " ", t)               # drop tags
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _fetch_url_text(url: str, max_chars: int = 15000) -> str:
    try:
        r = requests.get(url, timeout=6, headers={"User-Agent": "JennyLocal/1.0"})
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        if not any(s in ct for s in ("text", "html", "json")):
            return ""
        txt = r.text
        if "html" in ct:
            txt = _strip_html(txt)
        return txt[:max_chars]
    except Exception:
        return ""

PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Jenny Prime — Local GUI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    :root{--bg:#0b0c10;--card:#0f1115;--fg:#e8e8e8;--mut:#aaa;--ok:#3fb950;--bad:#e5534b;--acc:#2b7a78;--br:#222}
    *{box-sizing:border-box}
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;background:var(--bg);color:var(--fg)}
    header{padding:10px 12px;background:#111;border-bottom:1px solid var(--br);display:flex;gap:10px;align-items:center;flex-wrap:wrap}
    .pill{display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border:1px solid var(--br);border-radius:999px;background:var(--card);font-size:13px}
    .dot{width:10px;height:10px;border-radius:50%;background:#777}.ok{background:var(--ok)}.bad{background:var(--bad)}
    main{max-width:980px;margin:0 auto;padding:14px}
    #log{height:62vh;overflow:auto;border:1px solid var(--br);border-radius:12px;padding:12px;background:var(--card)}
    .u,.a{margin:10px 0;white-space:pre-wrap}
    .u{color:#9fd3c7}.a{color:#f8f8f2}
    .ts{color:var(--mut);font-size:11px;margin-left:6px}
    form{display:flex;gap:10px;margin-top:12px;align-items:flex-start;flex-wrap:wrap}
    textarea{flex:1;min-width:300px;resize:vertical;min-height:52px;max-height:200px;border-radius:12px;border:1px solid #333;background:var(--card);color:var(--fg);padding:10px}
    button{padding:10px 14px;border:none;border-radius:12px;background:var(--acc);color:#fff;cursor:pointer}
    button:disabled{opacity:.6;cursor:not-allowed}
    .col{display:flex;flex-direction:column;gap:8px}
    .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
    input[type="text"]{border-radius:10px;border:1px solid #333;background:var(--card);color:var(--fg);padding:8px;min-width:260px}
    input[type="file"]{font-size:12px;color:var(--mut)}
    label{font-size:12px;color:#cfcfcf}
    .hint{font-size:12px;color:var(--mut)}
    .chips{display:flex;gap:6px;flex-wrap:wrap}
    .chip{background:#1a1d24;border:1px solid var(--br);border-radius:999px;padding:4px 8px;font-size:12px;color:#cfcfcf}
  </style>
</head>
<body>
<header>
  <span class="pill">voice:
    <label><input type="checkbox" id="voiceIn"> mic</label>
    <label><input type="checkbox" id="voiceOut" checked> speak</label>
    <select id="voiceSel" style="max-width:280px"></select>
    <label>rate <input type="range" id="rate" min="0.7" max="1.3" step="0.05" value="1.0"></label>
    <label>pitch <input type="range" id="pitch" min="0.8" max="1.4" step="0.05" value="1.0"></label>
  </span>
  <span class="pill hint">Enter = send · Shift+Enter = newline</span>
</header>

<main>
  <div id="log"></div>

  <div class="row" style="margin-top:10px">
    <input type="text" id="url" placeholder="https://example.com/article…" />
    <label><input type="checkbox" id="useWeb"> include URL content</label>
    <input type="file" id="files" multiple accept=".txt,.md,.json,.jsonl"/>
    <div class="chips" id="fileChips"></div>
  </div>
  <div class="hint">Uploads supported now: .txt, .md, .json, .jsonl (max 1 MB total). We’ll add PDFs later.</div>

  <form id="f">
    <textarea id="q" placeholder="Type to Jenny…" autofocus></textarea>
    <div class="col">
      <button id="send">Send</button>
    </div>
  </form>
</main>

<script>
document.addEventListener('DOMContentLoaded', ()=>{
  // Ensure status pills exist (avoid null reference)
  const hdr = document.querySelector('header') || document.body.insertBefore(document.createElement('header'), document.body.firstChild);
  if (!document.getElementById('dot') || !document.getElementById('stat') || !document.getElementById('model')) {
    hdr.insertAdjacentHTML('afterbegin', `
      <span class="pill"><span id="dot" class="dot"></span><span id="stat">checking…</span></span>
      <span class="pill">model: <strong id="model">—</strong></span>
    `);
  }

  // Refs
  const log   = document.getElementById('log');
  const q     = document.getElementById('q');
  const btn   = document.getElementById('send');
  const form  = document.getElementById('f');
  const dot   = document.getElementById('dot');
  const stat  = document.getElementById('stat');
  const model = document.getElementById('model');
  const urlEl = document.getElementById('url');
  const useWeb= document.getElementById('useWeb');
  const files = document.getElementById('files');
  const chips = document.getElementById('fileChips');
  const voiceIn  = document.getElementById('voiceIn');
  const voiceOut = document.getElementById('voiceOut');
  const voiceSel = document.getElementById('voiceSel');
  const rate     = document.getElementById('rate');
  const pitch    = document.getElementById('pitch');

  // Small client guards
  let busy = false;             // single-flight submit
  let lastUser = "";            // last user message
  let lastAssistant = "";       // last assistant reply

  // Voice prefs
  let voices = [];
  if (rate)  rate.value  = localStorage.getItem('jenny.rate')  || '1.0';
  if (pitch) pitch.value = localStorage.getItem('jenny.pitch') || '1.0';

  function ts(){ return new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}); }

  function add(role, text){
    const div = document.createElement('div');
    div.className = role === 'user' ? 'u' : 'a';
    const who = (role==='user'?'You':'Jenny');
    div.innerHTML = `<strong>${who}:</strong> ${text} <span class="ts">${ts()}</span>`;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;

    // TTS (optional)
    if (role==='assistant' && voiceOut?.checked && 'speechSynthesis' in window){
      const ut = new SpeechSynthesisUtterance(text);
      const v = (voices || []).find(v=>v.name === (voiceSel?.value || ''));
      if (v) ut.voice = v;
      if (rate)  ut.rate  = parseFloat(rate.value)  || 1.0;
      if (pitch) ut.pitch = parseFloat(pitch.value) || 1.0;
      speechSynthesis.cancel(); speechSynthesis.speak(ut);
    }

    // heartbeat refresh
    ping();
    if (stat && dot) { stat.textContent='online'; dot.classList.add('ok'); dot.classList.remove('bad'); }
  }

  // heartbeat
  async function ping(){
    try{
      const r = await fetch('/api/ping'); const j = await r.json();
      if (model) model.textContent = j.model || '—';
      if (stat)  stat.textContent  = j.ok ? `online ${j.rtt_ms} ms` : 'offline';
      if (dot)  { dot.classList.toggle('ok', !!j.ok); dot.classList.toggle('bad', !j.ok); }
    }catch{
      if (stat) stat.textContent='offline';
      if (dot) { dot.classList.remove('ok'); dot.classList.add('bad'); }
    }
  }
  setInterval(ping, 8000); ping();

  // file chips
  files?.addEventListener('change', ()=>{
    if (!chips) return;
    chips.innerHTML = '';
    let total = 0;
    for (const f of files.files){
      total += f.size;
      const c = document.createElement('span');
      c.className='chip'; c.textContent = `${f.name} (${Math.round(f.size/1024)} KB)`;
      chips.appendChild(c);
    }
    if (total > 1024*1024){
      const warn = document.createElement('span');
      warn.className='chip'; warn.style='background:#3a1e1e;border-color:#442;';
      warn.textContent='Too large (>1MB)';
      chips.appendChild(warn);
    }
  });

  // submit (Enter=send; Shift+Enter=newline) + echo/dup guards
  form.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const text = (q.value || '').trim();
    if(!text) return;

    if (busy) return;                 // single-flight
    if (text === lastAssistant) {     // avoid echo
      add('assistant','⚠️ (ignored echo)');
      return;
    }
    busy = true; btn.disabled = true; q.disabled = true;

    if(files?.files?.length){
      let total=0; for(const f of files.files) total += f.size;
      if(total > 1024*1024){ add('assistant','⚠️ upload too large (>1MB total)'); busy=false; btn.disabled=false; q.disabled=false; return; }
    }

    add('user', text);
    const readFile = f => new Promise((res, rej)=>{ const r=new FileReader(); r.onload=()=>res({name:f.name, content:r.result}); r.onerror=rej; r.readAsText(f); });
    const filePayload = [];
    if (files) for(const f of files.files){ filePayload.push(await readFile(f)); }

    try{
      const r = await fetch('/api/chat', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          text,
          url: (urlEl?.value || '').trim(),
          use_web: !!(useWeb?.checked),
          files: filePayload
        })
      });
      const j = await r.json();
      add('assistant', j.reply || '(no reply)');
      lastUser = text;
      lastAssistant = (j.reply || '');
    }catch(err){
      add('assistant', '⚠️ ' + err);
    }finally{
      busy = false;
      btn.disabled = false; q.disabled = false;
      q.value = ''; q.focus();
    }
  });

  q.addEventListener('keydown', (e)=>{
    if(e.key === 'Enter' && !e.shiftKey){
      e.preventDefault();
      form.requestSubmit();
    }
  });

  // voice picker
  function populateVoices(){
    if (!('speechSynthesis' in window) || !voiceSel) return;
    voices = speechSynthesis.getVoices();
    voiceSel.innerHTML = '';
    const preferred = ["Microsoft Aria","Microsoft Jenny","Google US English","Samantha","Zira","Female"];
    const opts = [...voices].sort((a,b)=>{
      const ap = preferred.some(p=>a.name.includes(p));
      const bp = preferred.some(p=>b.name.includes(p));
      if (ap && !bp) return -1; if (!ap && bp) return 1; return a.name.localeCompare(b.name);
    });
    for (const v of opts){
      const o = document.createElement('option');
      o.value = v.name; o.textContent = `${v.name} (${v.lang})`;
      voiceSel.appendChild(o);
    }
    const saved = localStorage.getItem('jenny.voice');
    if (saved && [...voiceSel.options].some(o=>o.value===saved)) voiceSel.value = saved;
    else {
      const pick = [...voiceSel.options].find(o=>/Aria|Jenny|Zira|Samantha|Female/i.test(o.value));
      if (pick) voiceSel.value = pick.value;
    }
  }
  if ('speechSynthesis' in window){ populateVoices(); speechSynthesis.onvoiceschanged = populateVoices; }
  voiceSel?.addEventListener('change', ()=>localStorage.setItem('jenny.voice', voiceSel.value));
  rate?.addEventListener('input',  ()=>localStorage.setItem('jenny.rate',  rate.value));
  pitch?.addEventListener('input', ()=>localStorage.setItem('jenny.pitch', pitch.value));

  // mic (optional)
  let rec = null;
  voiceIn?.addEventListener('change', ()=>{
    if(voiceIn.checked){
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if(!SR){ add('assistant','⚠️ voice input not supported in this browser'); voiceIn.checked=false; return; }
      rec = new SR(); rec.lang='en-US'; rec.interimResults=true; rec.continuous=true;
      rec.onresult = (ev)=>{ let txt=''; for(const r of ev.results){ txt += r[0].transcript; } q.value = txt.trim(); };
      rec.onend = ()=>{ if(voiceIn.checked){ rec.start(); } };
      rec.start();
    }else{
      if(rec){ rec.onend=null; try{rec.stop();}catch{} rec=null; }
    }
  });
});
</script>
</body>
</html>
"""

@APP.get("/")
def home():
    return render_template_string(PAGE)

@APP.get("/api/ping")
def api_ping():
    t0 = time.time()
    ok = False
    try:
        r = requests.get(f"{CHAT_BASE}/api/tags", timeout=2)
        r.raise_for_status()
        ok = True
    except Exception:
        ok = False
    rtt = int((time.time()-t0)*1000)
    return jsonify({"ok": ok, "rtt_ms": rtt, "model": CHAT_MODEL})

@APP.post("/api/chat")
def api_chat():
    import time as _t
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"reply": ""})

    # server-side echo/dup fences
    now = _t.time()
    if text == _state["last_user"] and (now - _state["t_user"]) < 1.5:
        return jsonify({"reply": ""})
    if _state["last_reply"] and text == _state["last_reply"]:
        return jsonify({"reply": ""})

    # Build optional context from URL + files
    ctx_chunks = []

    if data.get("use_web") and data.get("url"):
        url = data["url"].strip()
        if url.startswith("http://") or url.startswith("https://"):
            url_text = _fetch_url_text(url)
            if url_text:
                ctx_chunks.append(f"### URL: {url}\n{url_text}")
            else:
                ctx_chunks.append(f"### URL: {url}\n(unable to fetch or not text/html)")
        else:
            ctx_chunks.append(f"### URL provided was not http(s): {url}")

    files = data.get("files") or []
    total_chars = 0
    for f in files:
        name = (f.get("name") or "upload.txt")[:80]
        content = (f.get("content") or "")[:20000]
        total_chars += len(content)
        if total_chars > 60000:   # cap total
            break
        ctx_chunks.append(f"### FILE: {name}\n{content}")

    combined_ctx = ("\n\n".join(ctx_chunks)).strip()
    text_for_model = (f"### EXTRA CONTEXT\n{combined_ctx}\n\n### USER REQUEST\n{text}"
                      if combined_ctx else text)

    reply = ask(text_for_model)

    # remember for fences
    _state["last_user"]  = text
    _state["t_user"]     = now
    _state["last_reply"] = reply

    return jsonify({"reply": reply})

if __name__ == "__main__":
    APP.run(host="127.0.0.1", port=7860, debug=False)
