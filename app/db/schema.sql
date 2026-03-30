CREATE TABLE IF NOT EXISTS invite_codes (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    code  TEXT    UNIQUE NOT NULL,
    label TEXT    NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    display_name  TEXT    NOT NULL,
    is_instructor INTEGER NOT NULL DEFAULT 0,
    invite_code_id INTEGER REFERENCES invite_codes(id),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conversations (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id               INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title                  TEXT    NOT NULL,
    created_at             TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at             TEXT    NOT NULL DEFAULT (datetime('now')),
    shared_with_instructor INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id     INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role                TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
    content             TEXT    NOT NULL,
    attachment_filename TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);
