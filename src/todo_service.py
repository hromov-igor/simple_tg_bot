from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import aiosqlite


@dataclass
class Todo:
    id: int
    user_id: int
    text: str
    done: bool
    created_at: datetime


class TodoService:
    def __init__(self, db_path: Path = Path("todo.sqlite3")):
        self.db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL
                )
                """
            )
            await db.commit()

    async def add(self, user_id: int, text: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO todos (user_id, text, done, created_at) VALUES (?, ?, 0, DATETIME('now'))",
                (user_id, text),
            )
            await db.commit()

    async def mark_done(self, user_id: int, todo_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE todos SET done = 1 WHERE id = ? AND user_id = ?",
                (todo_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def list_page(self, user_id: int, page: int, page_size: int = 10) -> Tuple[List[Todo], int]:

        offset = (page - 1) * page_size
        async with aiosqlite.connect(self.db_path) as db:

            cur = await db.execute(
                """
                WITH base AS (
                SELECT id, user_id, text, done, created_at,
                        COUNT(*) OVER() AS total_count
                FROM todos
                WHERE user_id = ?
                )
                SELECT id, user_id, text, done, created_at, total_count
                FROM base
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                """,
                (user_id, page_size, offset),
            )
            rows = await cur.fetchall()

            total_count = int(rows[0][5]) if rows else 0
            items: List[Todo] = list(
                map(
                    lambda row:
                        Todo(
                            id=row[0],
                            user_id=row[1],
                            text=row[2],
                            done=bool(row[3]),
                            created_at=datetime.fromisoformat(row[4]),
                        ),
                    rows,
                )
            )
            return items, int(total_count)
