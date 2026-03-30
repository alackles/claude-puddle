import os
from app.config import settings

# Context window budget (tokens). Anthropic claude-sonnet-4-6 supports 200k input tokens.
# We reserve a generous slice for system prompt + TOC + tool results + response headroom.
MAX_HISTORY_MESSAGES = 40


def load_system_prompt() -> str:
    path = os.path.join(settings.context_dir, "system_prompt.md")
    with open(path) as f:
        return f.read().strip()


def load_toc() -> str:
    path = os.path.join(settings.context_dir, "toc.md")
    with open(path) as f:
        return f.read().strip()


def build_system_prompt() -> str:
    system_prompt = load_system_prompt()
    toc = load_toc()
    return f"{system_prompt}\n\n---\n\n## Textbook Table of Contents\n\n{toc}"


def truncate_history(messages: list[dict], max_messages: int = MAX_HISTORY_MESSAGES) -> tuple[list[dict], bool]:
    """
    Return (truncated_messages, was_truncated).
    Drops oldest messages when history exceeds max_messages.
    Always keeps at least the most recent exchange.
    """
    if len(messages) <= max_messages:
        return messages, False
    return messages[-max_messages:], True
