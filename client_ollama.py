import os, json, requests

def get_config():
    base  = os.getenv("JENNY_BASE",  "http://127.0.0.1:11435")
    model = os.getenv("JENNY_MODEL", "fast")
    opts = {
        "num_ctx": int(os.getenv("JENNY_NUM_CTX", "512")),
        "num_predict": int(os.getenv("JENNY_NUM_PREDICT", "96")),
        "num_thread": int(os.getenv("JENNY_THREADS", "4")),
        "temperature": float(os.getenv("JENNY_TEMP", "0.2")),
        "top_p": float(os.getenv("JENNY_TOP_P", "0.9")),
        "seed": int(os.getenv("JENNY_SEED", "42")),

        # ---- ONE CHANGE: anti-repetition controls ----
        "repeat_penalty": float(os.getenv("JENNY_REPEAT_PENALTY", "1.22")),
        "repeat_last_n": int(os.getenv("JENNY_REPEAT_LAST_N", "192")),
    }
    return base, model, opts

# rest of file unchanged (chat_once, chat_stream, warm)
