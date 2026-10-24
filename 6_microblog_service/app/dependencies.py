from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Annotated

from app.database import get_db
from app.models import User, Tweet


async def get_current_user(
        api_key: Annotated[str, Header(alias="api-key")],
        db: AsyncSession = Depends(get_db)
) -> User:
    """Проверяет наличие api-key в заголовках и ищет пользователя в БД"""
    result = await db.execute(select(User).where(User.api_key == api_key))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверный API ключ или пользователь не найден"
        )
    return user


async def get_tweet_by_id(tweet_id: int,
                          db: AsyncSession = Depends(get_db)) -> Tweet:
    """Общая зависимость для поиска твита по ID с подгрузкой лайков"""
    query = (select(Tweet).options(selectinload(Tweet.likes))
             .where(Tweet.id == tweet_id))
    result = await db.execute(query)
    tweet = result.scalars().first()

    if not tweet:
        raise HTTPException(status_code=404, detail="Твит не найден")
    return tweet
