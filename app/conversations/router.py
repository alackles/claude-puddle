from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
import aiosqlite
from app.db.connection import get_db
from app.db.queries import (
    get_conversations_for_user,
    get_conversation,
    create_conversation,
    delete_conversation,
    rename_conversation,
    get_messages_for_conversation,
)
from app.auth.dependencies import get_current_user
from app.models.schemas import ConversationCreateRequest, ConversationRenameRequest, ConversationResponse, MessageResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    rows = await get_conversations_for_user(db, user["id"])
    return [
        ConversationResponse(
            id=row["id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            shared_with_instructor=bool(row["shared_with_instructor"]),
        )
        for row in rows
    ]


@router.post("", response_model=ConversationResponse)
async def create_new_conversation(
    body: ConversationCreateRequest,
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    conv_id = await create_conversation(db, owner_id=user["id"], title=body.title)
    row = await get_conversation(db, conv_id)
    return ConversationResponse(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        shared_with_instructor=bool(row["shared_with_instructor"]),
    )


@router.get("/{conversation_id}", response_model=dict)
async def get_conversation_with_messages(
    conversation_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    conv = await get_conversation(db, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv["owner_id"] != user["id"] and not user["is_instructor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await get_messages_for_conversation(db, conversation_id)
    return {
        "conversation": ConversationResponse(
            id=conv["id"],
            title=conv["title"],
            created_at=conv["created_at"],
            updated_at=conv["updated_at"],
            shared_with_instructor=bool(conv["shared_with_instructor"]),
        ),
        "messages": [
            MessageResponse(
                id=m["id"],
                role=m["role"],
                content=m["content"],
                attachment_filename=m["attachment_filename"],
                created_at=m["created_at"],
            )
            for m in messages
        ],
    }


@router.patch("/{conversation_id}")
async def rename_conversation_endpoint(
    conversation_id: int,
    body: ConversationRenameRequest,
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    conv = await get_conversation(db, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot be empty")

    await rename_conversation(db, conversation_id, title)
    return {"message": "Renamed"}


@router.delete("/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    conv = await get_conversation(db, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    await delete_conversation(db, conversation_id)
    return {"message": "Deleted"}


@router.get("/{conversation_id}/export")
async def export_conversation(
    conversation_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    conv = await get_conversation(db, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = await get_messages_for_conversation(db, conversation_id)

    lines = [f"# {conv['title']}", f"*Exported from Claude Puddle*", ""]
    for m in messages:
        role_label = "**You**" if m["role"] == "user" else "**Assistant**"
        if m["attachment_filename"]:
            lines.append(f"{role_label} *(attached: {m['attachment_filename']})*")
        else:
            lines.append(role_label)
        lines.append("")
        lines.append(m["content"])
        lines.append("")

    md_content = "\n".join(lines)
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in conv["title"])
    filename = f"{safe_title}.md"

    return PlainTextResponse(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
