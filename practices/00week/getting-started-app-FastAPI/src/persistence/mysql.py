import os
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiomysql


def _read_env_or_file(env_var: str, file_var: str, default: str = "") -> str:
    file_path = os.getenv(file_var)
    if file_path and os.path.exists(file_path):
        return Path(file_path).read_text().strip()
    return os.getenv(env_var, default)


_pool: Optional[aiomysql.Pool] = None


async def init() -> None:
    global _pool
    host = _read_env_or_file("MYSQL_HOST", "MYSQL_HOST_FILE", "localhost")
    user = _read_env_or_file("MYSQL_USER", "MYSQL_USER_FILE", "root")
    password = _read_env_or_file("MYSQL_PASSWORD", "MYSQL_PASSWORD_FILE", "")
    database = _read_env_or_file("MYSQL_DB", "MYSQL_DB_FILE", "todos")

    # Simple retry loop for MySQL readiness
    for attempt in range(10):
        try:
            _pool = await aiomysql.create_pool(
                host=host,
                port=3306,
                user=user,
                password=password,
                db=database,
                charset="utf8mb4",
                autocommit=True,
                minsize=1,
                maxsize=5,
            )
            break
        except Exception:
            await asyncio.sleep(1)

    if not _pool:
        raise RuntimeError("Failed to connect to MySQL database.")

    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "CREATE TABLE IF NOT EXISTS todo_items (id varchar(36), name varchar(255), completed boolean) DEFAULT CHARSET utf8mb4"
            )
    print(f"Connected to mysql db at host {host}")


async def teardown() -> None:
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def get_items() -> List[Dict[str, Any]]:
    assert _pool is not None
    async with _pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM todo_items")
            rows = await cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "completed": bool(row["completed"]),
                }
                for row in rows
            ]


async def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    assert _pool is not None
    async with _pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM todo_items WHERE id=%s", (item_id,))
            row = await cur.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "name": row["name"],
                "completed": bool(row["completed"]),
            }


async def store_item(item: Dict[str, Any]) -> None:
    assert _pool is not None
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO todo_items (id, name, completed) VALUES (%s, %s, %s)",
                (item["id"], item["name"], 1 if item.get("completed") else 0),
            )


async def update_item(item_id: str, item: Dict[str, Any]) -> None:
    assert _pool is not None
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE todo_items SET name=%s, completed=%s WHERE id=%s",
                (item["name"], 1 if item.get("completed") else 0, item_id),
            )


async def remove_item(item_id: str) -> None:
    assert _pool is not None
    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM todo_items WHERE id=%s", (item_id,))
