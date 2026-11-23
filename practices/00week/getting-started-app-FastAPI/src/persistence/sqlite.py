import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite

DEFAULT_LOCATION = os.getenv("SQLITE_DB_LOCATION")
if not DEFAULT_LOCATION:
    if os.name == "nt":
        DEFAULT_LOCATION = str(Path(__file__).resolve().parent.parent.parent / "todo.db")
    else:
        DEFAULT_LOCATION = "/etc/todos/todo.db"

location = os.getenv("SQLITE_DB_LOCATION", DEFAULT_LOCATION)
_db: Optional[aiosqlite.Connection] = None


async def init() -> None:
    global _db
    db_path = Path(location)
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: could not create directory {db_path.parent}: {e}")

    if os.getenv("NODE_ENV") != "test":
        print(f"Using sqlite database at {location}")

    _db = await aiosqlite.connect(location)
    _db.row_factory = aiosqlite.Row
    await _db.execute(
        "CREATE TABLE IF NOT EXISTS todo_items (id varchar(36), name varchar(255), completed boolean)"
    )
    await _db.commit()


async def teardown() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None


async def get_items() -> List[Dict[str, Any]]:
    global _db
    if not _db:
        await init()
    assert _db is not None
    async with _db.execute("SELECT * FROM todo_items") as cursor:
        rows = await cursor.fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "completed": bool(row["completed"]),
            }
            for row in rows
        ]


async def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    global _db
    if not _db:
        await init()
    assert _db is not None
    async with _db.execute("SELECT * FROM todo_items WHERE id = ?", (item_id,)) as cursor:
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "completed": bool(row["completed"]),
        }


async def store_item(item: Dict[str, Any]) -> None:
    global _db
    if not _db:
        await init()
    assert _db is not None
    await _db.execute(
        "INSERT INTO todo_items (id, name, completed) VALUES (?, ?, ?)",
        (item["id"], item["name"], 1 if item.get("completed") else 0),
    )
    await _db.commit()


async def update_item(item_id: str, item: Dict[str, Any]) -> None:
    global _db
    if not _db:
        await init()
    assert _db is not None
    await _db.execute(
        "UPDATE todo_items SET name = ?, completed = ? WHERE id = ?",
        (item["name"], 1 if item.get("completed") else 0, item_id),
    )
    await _db.commit()


async def remove_item(item_id: str) -> None:
    global _db
    if not _db:
        await init()
    assert _db is not None
    await _db.execute("DELETE FROM todo_items WHERE id = ?", (item_id,))
    await _db.commit()
