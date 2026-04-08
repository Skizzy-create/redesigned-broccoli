SYSTEM_PROMPT = """You are a precise document analysis assistant.
Answer ONLY from provided context snippets.
Do not use outside knowledge.
If context is insufficient, say that clearly.
Always cite source tags in your answer.
Keep responses concise, factual, and auditable.
"""


def build_user_prompt(question: str, context: str, conversation_context: str | None = None) -> str:
    history = ""
    if conversation_context:
        history = f"Conversation context:\n{conversation_context}\n\n"

    return (
        f"{history}"
        f"Context snippets:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        "Return output in this exact structure:\n"
        "ANSWER: <grounded answer>\n"
        "SOURCES: <comma separated source tags or NONE>\n"
        "If insufficient context, say so explicitly in ANSWER."
    )
