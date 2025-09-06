# chat_loop.py — streaming CLI with echo-guard + dynamic recall
import os, sys, json, requests
from memory_store import MEM
from prompt_builder import build_system_prompt

BASE  = os.getenv("JENNY_BASE",  "http://127.0.0.1:11435")
MODEL = os.getenv("JENNY_MODEL", "jenny:latest")
GEN_OPTS = {
    "num_ctx": int(os.getenv("JENNY_NUM_CTX", "2048")),
    "num_predict": int(os.getenv("JENNY_NUM_PREDICT", "256")),
    "num_thread": int(os.getenv("JENNY_THREADS", "4")),
    "repeat_penalty": float(os.getenv("JENNY_REPEAT_PENALTY", "1.1")),
    "repeat_last_n": int(os.getenv("JENNY_REPEAT_LAST_N", "128")),
}

# conversation state + echo guard
CONVO = []
LAST_ASSISTANT = ""

def _health_check():
    try:
        r = requests.get(f"{BASE}/api/tags", timeout=2)
        return r.ok
    except Exception:
        return False

def _tok(s: str) -> int:
    return max(1, len(s) // 4)

def _trim_convo(msgs, budget=900):
    used, out = 0, []
    for m in reversed(msgs):
        t = _tok(m.get("content", ""))
        if used + t > budget:
            break
        out.append(m)
        used += t
    return list(reversed(out))

def ask(user_text: str) -> str:
    global LAST_ASSISTANT, CONVO

    txt = (user_text or "").strip()
    if not txt:
        return ""

    # --- ECHO GUARD: ignore if our last reply bounced back as input
    if LAST_ASSISTANT and txt == LAST_ASSISTANT.strip():
        return "(ignored echo)"

    # log user turn
    MEM.update_from_turn("user", txt)

    # build system prompt with dynamic related recall
    sys_prompt = build_system_prompt(related_query=txt, recent_n=3)


    # compose the message window (small for speed)
    convo_win = _trim_convo(CONVO + [{"role": "user", "content": txt}], budget=900)

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": sys_prompt}] + convo_win,
        "options": GEN_OPTS,
        "stream": True,
    }

    buf = []
    try:
        with requests.post(f"{BASE}/api/chat", json=payload, stream=True, timeout=120) as r:
            if r.status_code == 404:
                raise RuntimeError("chat endpoint not available (404)")
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                delta = (obj.get("message") or {}).get("content", "")
                if delta:
                    sys.stdout.write(delta)
                    sys.stdout.flush()
                    buf.append(delta)
                if obj.get("done"):
                    break
    except Exception:
        # fallback to non-streaming generate
        prompt = f"{sys_prompt}\n\nUser: {txt}\nAssistant:"
        gen_payload = {"model": MODEL, "prompt": prompt, "options": GEN_OPTS, "stream": False}
        rr = requests.post(f"{BASE}/api/generate", json=gen_payload, timeout=120)
        rr.raise_for_status()
        buf.append((rr.json() or {}).get("response", ""))

    ans = "".join(buf).strip()

    # update state + memory
    if ans:
        MEM.update_from_turn("assistant", ans)
        CONVO.append({"role": "user", "content": txt})
        CONVO.append({"role": "assistant", "content": ans})
        LAST_ASSISTANT = ans

    return ans

if __name__ == "__main__":
    print("Jenny local chat (streaming). Ctrl+C to exit.")
    if not _health_check():
        print(f"⚠️ Ollama server not reachable at {BASE}")
    try:
        while True:
            q = input("\nYou: ").strip()
            if not q:
                continue
            print("\nJenny: ", end="", flush=True)
            a = ask(q)
            if a == "(ignored echo)":
                print("(ignored echo)")
            else:
                print()  # newline after streaming
    except KeyboardInterrupt:
        print("\nBye")
