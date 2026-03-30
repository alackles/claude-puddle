from fastapi import Request, HTTPException, Depends
import aiosqlite
from app.auth.sessions import decode_session, COOKIE_NAME
from app.db.connection import get_db
from app.db.queries import get_user_by_id


async def get_current_user(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> aiosqlite.Row:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_session(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_instructor(
    user: aiosqlite.Row = Depends(get_current_user),
) -> aiosqlite.Row:
    if not user["is_instructor"]:
        raise HTTPException(status_code=403, detail="Instructor access required")
    return user
