import aiosqlite
from typing import Any


# --- Invite codes ---

async def get_invite_code(db: aiosqlite.Connection, code: str) -> aiosqlite.Row | None:
    async with db.execute(
        "SELECT * FROM invite_codes WHERE code = ? AND active = 1", (code,)
    ) as cursor:
        return await cursor.fetchone()


async def create_invite_code(db: aiosqlite.Connection, code: str, label: str) -> int:
    async with db.execute(
        "INSERT INTO invite_codes (code, label) VALUES (?, ?)", (code, label)
    ) as cursor:
        await db.commit()
        return cursor.lastrowid


async def deactivate_invite_code(db: aiosqlite.Connection, code: str):
    await db.execute("UPDATE invite_codes SET active = 0 WHERE code = ?", (code,))
    await db.commit()


# --- Users ---

async def get_user_by_email(db: aiosqlite.Connection, email: str) -> aiosqlite.Row | None:
    async with db.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ) as cursor:
        return await cursor.fetchone()


async def get_user_by_id(db: aiosqlite.Connection, user_id: int) -> aiosqlite.Row | None:
    async with db.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ) as cursor:
        return await cursor.fetchone()


async def create_user(
    db: aiosqlite.Connection,
    email: str,
    password_hash: str,
    display_name: str,
    invite_code_id: int,
    is_instructor: bool = False,
) -> int:
    async with db.execute(
        """INSERT INTO users (email, password_hash, display_name, invite_code_id, is_instructor)
           VALUES (?, ?, ?, ?, ?)""",
        (email, password_hash, display_name, invite_code_id, int(is_instructor)),
    ) as cursor:
        await db.commit()
        return cursor.lastrowid


async def update_user_password(db: aiosqlite.Connection, user_id: int, password_hash: str):
    await db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id)
    )
    await db.commit()


# --- Conversations ---

async def get_conversations_for_user(db: aiosqlite.Connection, user_id: int) -> list[aiosqlite.Row]:
    async with db.execute(
        "SELECT * FROM conversations WHERE owner_id = ? ORDER BY updated_at DESC", (user_id,)
    ) as cursor:
        return await cursor.fetchall()


async def get_conversation(db: aiosqlite.Connection, conversation_id: int) -> aiosqlite.Row | None:
    async with db.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ) as cursor:
        return await cursor.fetchone()


async def create_conversation(db: aiosqlite.Connection, owner_id: int, title: str) -> int:
    async with db.execute(
        "INSERT INTO conversations (owner_id, title) VALUES (?, ?)", (owner_id, title)
    ) as cursor:
        await db.commit()
        return cursor.lastrowid


async def delete_conversation(db: aiosqlite.Connection, conversation_id: int):
    await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    await db.commit()


async def touch_conversation(db: aiosqlite.Connection, conversation_id: int):
    await db.execute(
        "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
        (conversation_id,),
    )
    await db.commit()


async def set_shared_with_instructor(db: aiosqlite.Connection, conversation_id: int, shared: bool):
    await db.execute(
        "UPDATE conversations SET shared_with_instructor = ? WHERE id = ?",
        (int(shared), conversation_id),
    )
    await db.commit()


async def get_shared_conversations(db: aiosqlite.Connection) -> list[aiosqlite.Row]:
    async with db.execute(
        """SELECT c.*, u.email as owner_email, u.display_name as owner_display_name
           FROM conversations c
           JOIN users u ON c.owner_id = u.id
           WHERE c.shared_with_instructor = 1
           ORDER BY c.updated_at DESC"""
    ) as cursor:
        return await cursor.fetchall()


# --- Messages ---

async def get_messages_for_conversation(
    db: aiosqlite.Connection, conversation_id: int
) -> list[aiosqlite.Row]:
    async with db.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    ) as cursor:
        return await cursor.fetchall()


async def create_message(
    db: aiosqlite.Connection,
    conversation_id: int,
    role: str,
    content: str,
    attachment_filename: str | None = None,
) -> int:
    async with db.execute(
        """INSERT INTO messages (conversation_id, role, content, attachment_filename)
           VALUES (?, ?, ?, ?)""",
        (conversation_id, role, content, attachment_filename),
    ) as cursor:
        await db.commit()
        return cursor.lastrowid
