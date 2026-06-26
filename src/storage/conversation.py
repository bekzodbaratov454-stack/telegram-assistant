"""Suhbat tarixini SQLite da saqlash."""

from __future__ import annotations

import aiosqlite
from pathlib import Path


class ConversationStore:
    def __init__(self, db_path: str | Path, max_messages: int = 20) -> None:
        self._db_path = Path(db_path)
        self._max_messages = max_messages
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, id)"
            )
            await db.commit()

    async def add_message(self, chat_id: int, role: str, content: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content),
            )
            await db.commit()
        await self._trim(chat_id)

    async def get_history(self, chat_id: int) -> list[dict[str, str]]:
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT role, content FROM messages
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, self._max_messages),
            )
            rows = await cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    async def clear_chat(self, chat_id: int) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            await db.commit()

    async def _trim(self, chat_id: int) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                DELETE FROM messages
                WHERE chat_id = ? AND id NOT IN (
                    SELECT id FROM messages
                    WHERE chat_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (chat_id, chat_id, self._max_messages),
            )
            await db.commit()
