#!/usr/bin/env python3
"""
Manage invite codes in the Claude Puddle database.

Usage:
  python scripts/seed_invite_code.py add <code> <label>
  python scripts/seed_invite_code.py deactivate <code>
  python scripts/seed_invite_code.py list
"""

import sqlite3
import sys
import os

DB_PATH = os.environ.get("DB_PATH", "/data/db.sqlite3")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def cmd_add(code: str, label: str):
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO invite_codes (code, label, active) VALUES (?, ?, 1)",
                (code, label),
            )
            conn.commit()
            print(f"Added invite code '{code}' ({label})")
        except sqlite3.IntegrityError:
            print(f"Error: invite code '{code}' already exists")
            sys.exit(1)


def cmd_deactivate(code: str):
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE invite_codes SET active = 0 WHERE code = ?", (code,)
        )
        conn.commit()
        if cur.rowcount == 0:
            print(f"Error: invite code '{code}' not found")
            sys.exit(1)
        print(f"Deactivated invite code '{code}'")


def cmd_list():
    with get_db() as conn:
        rows = conn.execute("SELECT code, label, active FROM invite_codes ORDER BY id").fetchall()
        if not rows:
            print("No invite codes.")
            return
        print(f"{'Code':<30} {'Label':<30} {'Active'}")
        print("-" * 70)
        for row in rows:
            active = "yes" if row["active"] else "no"
            print(f"{row['code']:<30} {row['label']:<30} {active}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "add":
        if len(sys.argv) != 4:
            print("Usage: seed_invite_code.py add <code> <label>")
            sys.exit(1)
        cmd_add(sys.argv[2], sys.argv[3])
    elif cmd == "deactivate":
        if len(sys.argv) != 3:
            print("Usage: seed_invite_code.py deactivate <code>")
            sys.exit(1)
        cmd_deactivate(sys.argv[2])
    elif cmd == "list":
        cmd_list()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
