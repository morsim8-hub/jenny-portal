import json, pathlib
BASE = pathlib.Path(__file__).resolve().parent
SYSTEM_PROMPT_TXT = BASE / "system_prompt.txt"
PROFILE_JSON      = BASE / "memory" / "profile.json"

def load_bootstrap_prompt():
    try:
        core = SYSTEM_PROMPT_TXT.read_text(encoding="utf-8").strip()
    except Exception:
        core = "You are Jenny Prime. Stay aligned, concise, kind."
    facts = []
    try:
        p = json.loads(PROFILE_JSON.read_text(encoding="utf-8"))
        for k, v in p.items():
            facts.append(f"- {k}: {v}")
    except Exception:
        pass
    facts_block = "Persistent facts:\n" + ("\n".join(facts) if facts else "- (no facts yet)")
    return core + "\n\n" + facts_block
