from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from app.db.connection import get_db
from app.db.queries import get_conversation, set_shared_with_instructor, get_shared_conversations
from app.auth.dependencies import get_current_user, require_instructor
from app.models.schemas import ConversationResponse

router = APIRouter(tags=["sharing"])


@router.post("/conversations/{conversation_id}/share")
async def share_conversation(
    conversation_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    user: aiosqlite.Row = Depends(get_current_user),
):
    conv = await get_conversation(db, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv["owner_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    await set_shared_with_instructor(db, conversation_id, shared=True)
    return {"message": "Shared with instructor"}


@router.get("/shared", response_model=list[ConversationResponse])
async def list_shared_conversations(
    db: aiosqlite.Connection = Depends(get_db),
    _: aiosqlite.Row = Depends(require_instructor),
):
    rows = await get_shared_conversations(db)
    return [
        ConversationResponse(
            id=row["id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            shared_with_instructor=True,
            owner_email=row["owner_email"],
            owner_display_name=row["owner_display_name"],
        )
        for row in rows
    ]
