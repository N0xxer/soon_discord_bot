import aiosqlite

DB_PATH = "dbs/main.db"


async def init_db():
    """Создает необходимые таблицы при первом запуске бота."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS voice_configs (
                user_id INTEGER PRIMARY KEY,
                name TEXT DEFAULT NULL,
                user_limit INTEGER DEFAULT NULL,
                private INTEGER DEFAULT 0,
                blocked_users TEXT DEFAULT NULL,
                vc_channels_ids TEXT DEFAULT NULL
            )
        """)
        await db.commit()


async def get_user_info(user_id: int, info_type: str):
    """Получает информацию о пользователе из БД."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT {info_type} FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            
            # Если пользователя нет в базе, создаем запись
            await db.execute(
                f"INSERT INTO users (user_id) VALUES (?)", 
                (user_id,)
            )
            await db.commit()
            return 0


async def update_user_info(user_id: int, info_type: str, amount: str):
    """Обновляет информацию о пользователе."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE users SET {info_type} = ? WHERE user_id = ?", 
            (amount, user_id)
        )
        await db.commit()


async def get_voice_config(user_id: int, info_type: str):
    """Получает конфигурацию голосового канала пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT {info_type} FROM voice_configs WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            return None


async def update_voice_config(user_id: int, info_type: str, value):
    """Обновляет конфигурацию голосового канала пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"INSERT INTO voice_configs (user_id, {info_type}) VALUES (?, ?) "
            f"ON CONFLICT(user_id) DO UPDATE SET {info_type} = excluded.{info_type}",
            (user_id, value)
        )
        await db.commit()


async def get_owner_by_channel_id(channel_id: int):
    """Находит user_id владельца по ID голосового канала."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id FROM voice_configs WHERE vc_channels_ids = ?",
            (str(channel_id),),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def clear_channel_owner(channel_id: int):
    """Сбрасывает ID канала у владельца при удалении комнаты."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE voice_configs SET vc_channels_ids = NULL WHERE vc_channels_ids = ?",
            (str(channel_id),),
        )
        await db.commit()