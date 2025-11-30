import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

async def test_connection():
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://botgpt:botgpt123@localhost:5432/botgpt")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())