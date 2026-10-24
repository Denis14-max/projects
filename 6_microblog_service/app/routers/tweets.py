from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from app.database import get_db
from app.models import User, Tweet, Media, likes_table
from app.schemas import TweetIn, TweetCreateResponse, TweetListResponse, SuccessResponse
from app.dependencies import get_current_user, get_tweet_by_id

router = APIRouter(prefix="/api/tweets", tags=["Твиты и Лайки"])


@router.post("", response_model=TweetCreateResponse, summary="Создать твит")
async def create_tweet(
        tweet_data: TweetIn,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
) -> TweetCreateResponse:
    """Создает новый твит и привязывает к нему медиафайлы"""
    new_tweet = Tweet(
        content=tweet_data.tweet_data,
        author_id=user.id,
    )
    db.add(new_tweet)
    await db.flush()

    if tweet_data.tweet_media_ids:
        result = await db.execute(select(Media).where(Media.id.in_(tweet_data.tweet_media_ids)))
        medias = result.scalars().all()
        for media in medias:
            media.tweet_id = new_tweet.id

    await db.commit()
    return TweetCreateResponse(result=True, tweet_id=new_tweet.id)


@router.get("", response_model=TweetListResponse, summary="Получить ленту твитов")
async def get_tweets(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Получение ленты твитов от пользователей, на которых подписан юзер (плюс свои)"""
    user_query = select(User).options(selectinload(User.following)).where(User.id == user.id)
    user_result = await db.execute(user_query)
    curr_user = user_result.scalars().first()

    authors_ids = [u.id for u in curr_user.following]
    authors_ids.append(user.id)

    query = (
        select(Tweet)
        .options(
            selectinload(Tweet.author),
            selectinload(Tweet.likes),
            selectinload(Tweet.attachments)
        )
        .outerjoin(likes_table, Tweet.id == likes_table.c.tweet_id)
        .where(Tweet.author_id.in_(authors_ids))
        .group_by(Tweet.id)
        .order_by(
            func.count(likes_table.c.user_id).desc(),
            Tweet.created_at.desc()
        )
    )

    result = await db.execute(query)
    tweets = result.scalars().all()
    return TweetListResponse(result=True, tweets=tweets)


@router.post("/{tweet_id}/likes", response_model=SuccessResponse, summary="Поставить лайк")
async def like_tweet(
        tweet: Tweet = Depends(get_tweet_by_id),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Ставит лайк на твит"""
    already_liked = any(liked_user.id == user.id for liked_user in tweet.likes)
    if not already_liked:
        tweet.likes.append(user)
        await db.commit()
    return SuccessResponse(result=True)


@router.delete("/{tweet_id}/likes", response_model=SuccessResponse, summary="Убрать лайк")
async def unlike_tweet(
        tweet: Tweet = Depends(get_tweet_by_id),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Убирает лайк с твита"""
    for liked_user in tweet.likes:
        if liked_user.id == user.id:
            tweet.likes.remove(liked_user)
            await db.commit()
            break
    return SuccessResponse(result=True)


@router.delete("/{tweet_id}", response_model=SuccessResponse, summary="Удалить твит")
async def delete_tweet(
        tweet: Tweet = Depends(get_tweet_by_id),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Удаляет твит (только если автор — текущий пользователь)"""
    if tweet.author_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Вы можете удалять только свои собственные твиты"
        )
    await db.delete(tweet)
    await db.commit()
    return SuccessResponse(result=True)
