from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import aiosqlite
from app.db.connection import get_db
from app.db.queries import (
    get_conversation,
    get_messages_for_conversation,
    create_message,
    touch_conversation,
)
from app.auth.dependencies import get_current_user
from app.models.schemas import MessageRequest
from app.chat.anthropic_client import stream_response, EVT_DONE

router = APIRouter(tags=["chat"])


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    body: MessageRequest,
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    conv = await get_conversation(db, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Build the user message content (with optional file attachment inline)
    user_content = body.content
    if body.attachment_content and body.attachment_filename:
        user_content = (
            f"[Attached file: {body.attachment_filename}]\n\n"
            f"```\n{body.attachment_content}\n```\n\n"
            f"{body.content}"
        )

    # Save user message to DB
    await create_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=body.content,
        attachment_filename=body.attachment_filename,
    )
    await touch_conversation(db, conversation_id)

    # Load history (excluding the message we just saved — we pass user_content directly)
    history = await get_messages_for_conversation(db, conversation_id)
    # The last message is the one we just saved; pass history minus that for context
    prior_history = list(history[:-1])

    # We need to persist the assistant response after streaming completes.
    # Collect the full response while streaming.
    full_response: list[str] = []

    async def event_stream():
        async for chunk in stream_response(prior_history, user_content):
            yield chunk
            # Extract final text from EVT_DONE to persist
            if chunk.startswith("event: done\n"):
                data_line = chunk.split("\ndata: ", 1)[1].rstrip("\n")
                full_response.append(data_line)

        # Persist assistant response after stream ends
        if full_response:
            await create_message(
                db,
                conversation_id=conversation_id,
                role="assistant",
                content=full_response[0],
            )
            await touch_conversation(db, conversation_id)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
