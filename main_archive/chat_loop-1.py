# chat_loop.py — streaming CLI with echo-guard
import os, sys, json, requests, time
from memory_store import MEM
from prompt_builder import build_system_prompt

BASE  = os.getenv("JENNY_BASE",  "http://localhost:11435")
MODEL = os.getenv("JENNY_MODEL", "jenny:latest")
GEN_OPTS = {
    "num_ctx": int(os.getenv("JENNY_NUM_CTX", "512")),
    "num_predict": int(os.getenv("JENNY_NUM_PREDICT", "128")),
    "num_thread": int(os.getenv("JENNY_THREADS", "4")),
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

def ask(user_text: str) -> str:
    global LAST_ASSISTANT

    txt = (user_text or "").strip()
    if not txt:
        return ""

    # --- ECHO GUARD: don't answer our last reply if it bounced back
    if LAST_ASSISTANT and txt == LAST_ASSISTANT.strip():
        return "(ignored echo)"

    MEM.update_from_turn("user", txt)
    sys_prompt = build_system_prompt()

    # Append user message to convo we send (assistant gets appended after)
    convo_msgs = CONVO + [{"role": "user", "content": txt}]
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": sys_prompt}] + convo_msgs,
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
                delta = obj.get("message", {}).get("content", "")
                if delta:
                    sys.stdout.write(delta)
                    sys.stdout.flush()
                    buf.append(delta)
                if obj.get("done"):
                    break
    except Exception:
        # Fallback to non-streaming generate
        prompt = f"{sys_prompt}\n\nUser: {txt}\nAssistant:"
        gen_payload = {"model": MODEL, "prompt": prompt, "options": GEN_OPTS, "stream": False}
        rr = requests.post(f"{BASE}/api/generate", json=gen_payload, timeout=120)
        rr.raise_for_status()
        buf.append(rr.json().get("response", ""))

    ans = "".join(buf).strip()

    # Update state + memory
    if ans:
        MEM.update_from_turn("assistant", ans)
        CONVO.append({"role": "user", "content": txt})
        CONVO.append({"role": "assistant", "content": ans})
        LAST_ASSISTANT = ans

    return ans

if __name__ == "__main__":
    print("Jenny local chat (streaming). Ctrl+C to exit.")
    if not _health_check():
        print("⚠️ Ollama server not reachable at", BASE)
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
