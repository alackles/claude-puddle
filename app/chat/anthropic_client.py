import json
from typing import AsyncGenerator
import anthropic
from app.config import settings
from app.chat.tools import TOOLS, resolve_chapter
from app.chat.context import build_system_prompt, truncate_history

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

# SSE event types sent to the front-end
EVT_TOKEN = "token"
EVT_TOOL_START = "tool_start"
EVT_TRUNCATED = "truncated"
EVT_DONE = "done"
EVT_ERROR = "error"


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


def _history_to_api(db_messages: list) -> list[dict]:
    """Convert DB message rows to Anthropic API message format."""
    result = []
    for m in db_messages:
        content = m["content"]
        if m["attachment_filename"] and m["role"] == "user":
            content = f"[Attached file: {m['attachment_filename']}]\n\n{content}"
        result.append({"role": m["role"], "content": content})
    return result


async def stream_response(
    db_messages: list,
    new_user_content: str,
) -> AsyncGenerator[str, None]:
    """
    Yield SSE-formatted strings. Handles the tool-use loop internally:
    1. Stream response; collect tool_use blocks if present.
    2. Resolve tool calls (chapter loading), send results back.
    3. Repeat until no tool_use in response; stream final text tokens to caller.
    """
    history, was_truncated = truncate_history(_history_to_api(db_messages))

    if was_truncated:
        yield _sse(EVT_TRUNCATED, "Earlier messages have been removed to fit the context window.")

    history.append({"role": "user", "content": new_user_content})
    system_prompt = build_system_prompt()

    # Tool-use loop — may iterate multiple times if Claude requests chapters
    while True:
        accumulated_text = ""
        tool_uses: list[dict] = []
        current_tool_use: dict | None = None

        try:
            async with client.messages.stream(
                model=settings.model,
                max_tokens=4096,
                system=system_prompt,
                tools=TOOLS,
                messages=history,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            yield _sse(EVT_TOOL_START, "Consulting the textbook...")
                            current_tool_use = {
                                "type": "tool_use",
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": "",
                            }
                        elif event.content_block.type == "text":
                            current_tool_use = None

                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            chunk = event.delta.text
                            accumulated_text += chunk
                            yield _sse(EVT_TOKEN, chunk)
                        elif event.delta.type == "input_json_delta" and current_tool_use:
                            current_tool_use["input"] += event.delta.partial_json

                    elif event.type == "content_block_stop":
                        if current_tool_use:
                            current_tool_use["input"] = json.loads(current_tool_use["input"] or "{}")
                            tool_uses.append(current_tool_use)
                            current_tool_use = None

                    elif event.type == "message_stop":
                        pass

        except anthropic.APIError as e:
            yield _sse(EVT_ERROR, str(e))
            return

        # If no tool use, we're done
        if not tool_uses:
            yield _sse(EVT_DONE, accumulated_text)
            return

        # Build assistant message with all content blocks (text + tool_use)
        assistant_content = []
        if accumulated_text:
            assistant_content.append({"type": "text", "text": accumulated_text})
        for tu in tool_uses:
            assistant_content.append({
                "type": "tool_use",
                "id": tu["id"],
                "name": tu["name"],
                "input": tu["input"],
            })

        history.append({"role": "assistant", "content": assistant_content})

        # Resolve tool calls and build tool results message
        tool_results = []
        for tu in tool_uses:
            if tu["name"] == "load_chapter":
                chapter_num = tu["input"].get("chapter_number", 0)
                content_block = resolve_chapter(chapter_num)
            else:
                content_block = {"type": "text", "text": f"Unknown tool: {tu['name']}"}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu["id"],
                "content": [content_block],
            })

        history.append({"role": "user", "content": tool_results})
        # Loop continues — stream next response from Claude
