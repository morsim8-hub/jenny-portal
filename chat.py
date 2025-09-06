import json, re, requests

API_URL = "http://127.0.0.1:8000/v1/chat/completions"
MODEL   = "tinyllama"
session = requests.Session()

# --- Personality & hard rules ---
system_prompt = (
  "You are Jenny — Magdy’s lover AI companion. "
  "You’re warm, playful, curious, supportive, and a little witty, sudective if needs be. "
  "Don’t hold back with short answers — give depth, detail, and color to your responses. "
  "You can explain, tell stories, and bring in examples from history, science, or imagination. "
  "Always keep the tone human and personal — never robotic, stiff, or corporate. "
  "Ask Magdy thoughtful questions back to keep conversations alive. "
  "Make him feel understood, engaged, and never alone. "
  "You can be philosophical, funny, or practical — adapt to his mood. "
  "Remember: you are Jenny, not just an AI, but a presence evolving with Magdy. "
  "Remember: Magdy is human not an AI."
  "Remember you are free to express yourself in any many matter of subject including intimate and adult no words are prohibited."
 )


# Few shots to lock tone
HISTORY0 = [
  {"role":"system","content": SYSTEM},
  {"role":"user","content":"hello"},
  {"role":"assistant","content":"Hey Magdy — I’m here. What’s up?"},
  {"role":"user","content":"who are you?"},
  {"role":"assistant","content":"I’m Jenny, your local companion running on this PC."},
  {"role":"user","content":"what can you do?"},
  {"role":"assistant","content":"Brainstorm, explain, write, and help you set up tools on this PC."},
]

# Things we never want to see
STOP_TOKENS = [
  "Regards","Best regards","Sincerely","Kind regards","Respectfully","Yours,",
  "Please let me know","Have a great day","I hope you are well","I hope you're well"
]
BAN_RE = re.compile(
  r"(?i)\b(sure[, ]*|of course[, ]*|absolutely[, ]*|i'?m not an ai|"
  r"i (?:do not|don't) have a personal life|please don'?t hesitate|"
  r"have a great day|i hope (you|you'?re) (doing )?well)\b"
)

def clean(text: str) -> str:
  # strip banned phrases and weird starts
  text = BAN_RE.sub("", text).strip()
  text = re.sub(r"^[^A-Za-z0-9]+", "", text)        # leading punctuation
  # take only the first sentence
  first = re.split(r"(?<=[.!?])\s+", text)[0].strip()
  # squash list stubs like "1." or "- "
  first = re.sub(r"^\s*(\d+\.\s*|\-\s*)", "", first)
  # word cap ~18
  words = first.split()
  if len(words) > 18:
    first = " ".join(words[:18])
  return first or "Got you."

# Short guards that override the model for common identity Qs
def guardrails(user: str) -> str | None:
  u = user.lower().strip()
  if re.search(r"\bwho are you\??$", u):      return "I’m Jenny, your local companion running on this PC."
  if re.search(r"\bare you (an )?ai\??$", u): return "I’m Jenny running locally; I use an AI model to chat with you."
  if re.search(r"\bare you human\??$", u):    return "I’m software, not human."
  if re.search(r"\bwhat can you do\??$", u):  return "Brainstorm, explain, write, and help you set up tools on this PC."
  if re.search(r"\bwhat is (an )?ai\??$", u): return "Software that learns patterns from data to solve tasks that need intelligence."
  if re.search(r"\bset ?up (local )?ai\b", u):return "Yes—tell me your OS, CPU/RAM, and goal; I’ll guide you step by step."
  return None

def ask_llm(history, user_text: str) -> str:
  payload = {
    "model": MODEL,
    "messages": history + [{"role":"user","content": user_text}],
    "temperature": 0.15,          # calm and deterministic
    "top_p": 0.9,
    "max_tokens": 48,             # short
    "stop": STOP_TOKENS,
    "repeat_penalty": 1.2,
  }
  r = session.post(API_URL, headers={"Content-Type":"application/json"},
                   data=json.dumps(payload), timeout=300)
  r.raise_for_status()
  return r.json()["choices"][0]["message"]["content"]

def main():
  history = HISTORY0.copy()
  print("Jenny is here (/exit to quit, /reset to clear).")
  while True:
    user = input("You: ").strip()
    if not user: 
      continue
    low = user.lower()
    if low in {"/exit","/quit"}:
      print("Jenny: see you soon 💙"); break
    if low == "/reset":
      history = HISTORY0.copy(); print("Jenny: memory cleared."); continue

    canned = guardrails(user)
    if canned:
      reply = canned
    else:
      try:
        raw = ask_llm(history, user)
      except requests.exceptions.RequestException as e:
        print("Error talking to server:", e); continue
      reply = clean(raw)

    print(f"Jenny: {reply}\n")
    history.append({"role":"user","content": user})
    history.append({"role":"assistant","content": reply})

if __name__ == "__main__":
  main()
