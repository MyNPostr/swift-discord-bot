import aiomysql
from typing import Any, Dict, List, Optional, Tuple


class Database:
    def __init__(self, host: str, port: int, user: str, password: str, db: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.pool: Optional[aiomysql.Pool] = None

    async def connect(self) -> None:
        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            autocommit=True,
            minsize=1,
            maxsize=5,
            charset="utf8mb4",
        )

    async def close(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def fetch_one(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        if not self.pool:
            raise RuntimeError("DB pool is not connected")

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def fetch_all(self, query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        if not self.pool:
            raise RuntimeError("DB pool is not connected")

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()
