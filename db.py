from __future__ import annotations

from typing import Optional

import aiosqlite


class FaqStorage:
    def __init__(self, path: str) -> None:
        self._path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS faqs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL
                )
                """
            )
            await db.commit()

    async def add(self, question: str, answer: str) -> int:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                "INSERT INTO faqs (question, answer) VALUES (?, ?)",
                (question, answer),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def list(self) -> list[tuple[int, str]]:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                "SELECT id, question FROM faqs ORDER BY id ASC"
            )
            rows = await cursor.fetchall()
            return [(int(row[0]), str(row[1])) for row in rows]

    async def get(self, faq_id: int) -> Optional[tuple[int, str, str]]:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                "SELECT id, question, answer FROM faqs WHERE id = ?",
                (faq_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return int(row[0]), str(row[1]), str(row[2])

    async def delete(self, faq_id: int) -> bool:
        async with aiosqlite.connect(self._path) as db:
            cursor = await db.execute(
                "DELETE FROM faqs WHERE id = ?",
                (faq_id,),
            )
            await db.commit()
            return cursor.rowcount > 0
