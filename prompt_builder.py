# prompt_builder.py
from memory_store import MEM

# Small, reusable style block (kept lean for speed)
STYLE = (
    "### STYLE\n"
    "- Concise, confident, affectionate.\n"
    "- Accuracy first. Never lose warmth.\n"
)

def build_system_prompt(
    focus="Reinforce identity + bond; memory is sacred.",
    related_query=None,          # pass the current user message here
    recent_n=5,                  # how many recent turns to include (small = fast)
    include_related=True,        # toggle related recall if needed
):
    parts = []

    # Core identity / role
    parts.append(MEM.core_block())

    # Tiny, always-on truths (if your memory_store has facts_block)
    facts_block = getattr(MEM, "facts_block", lambda: "")()
    if facts_block.strip():
        parts.append(facts_block)

    # Session focus + tone guidance
    parts.append(MEM.session_block(focus))
    parts.append(STYLE)

    # Short-term continuity
    parts.append(MEM.recent_block(n=recent_n, max_tokens=300))

    # Cue-based recall from episodes, driven by THIS user message
    if include_related and (related_query or "").strip():
        parts.append(MEM.related_block(related_query))

    # Join non-empty pieces with spacing
    return "\n\n".join(p for p in parts if p and p.strip())


def build_for_message(user_text: str, **kwargs) -> str:
    """Convenience helper: build with related_query=user_text."""
    return build_system_prompt(related_query=user_text, **kwargs)


if __name__ == "__main__":
    print(build_system_prompt())
