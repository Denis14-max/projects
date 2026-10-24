from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User
from app.schemas import UserResponse, UserProfileOut, UserBase, SuccessResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["Пользователи и Подписки"])


@router.get("/me", response_model=UserResponse, summary="Получить мой профиль")
async def get_my_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(User).options(
        selectinload(User.following),
        selectinload(User.followers)
    ).where(User.id == user.id)
    result = await db.execute(query)
    me = result.scalars().first()

    profile = UserProfileOut(
        id=me.id,
        name=me.name,
        followers=[UserBase(id=f.id, name=f.name) for f in me.followers],
        following=[UserBase(id=f.id, name=f.name) for f in me.following]
    )
    return UserResponse(result=True, user=profile)


@router.get("/{user_id}", response_model=UserResponse, summary="Профиль пользователя по ID")
async def get_user_profile(user_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(User).options(
        selectinload(User.following),
        selectinload(User.followers)
    ).where(User.id == user_id)
    result = await db.execute(query)
    target_user = result.scalars().first()

    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    profile = UserProfileOut(
        id=target_user.id,
        name=target_user.name,
        followers=[UserBase(id=f.id, name=f.name) for f in target_user.followers],
        following=[UserBase(id=f.id, name=f.name) for f in target_user.following]
    )
    return UserResponse(result=True, user=profile)


@router.post("/{user_id}/follow", response_model=SuccessResponse, summary="Подписаться на пользователя")
async def follow_user(user_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Нельзя подписаться на самого себя")

    result = await db.execute(select(User).where(User.id == user_id))
    user_to_follow = result.scalars().first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    query = select(User).options(selectinload(User.following)).where(User.id == current_user.id)
    curr_user_result = await db.execute(query)
    curr_user_with_follows = curr_user_result.scalars().first()

    already_following = any(u.id == user_id for u in curr_user_with_follows.following)
    if not already_following:
        curr_user_with_follows.following.append(user_to_follow)
        await db.commit()
    return SuccessResponse(result=True)


@router.delete("/{user_id}/follow", response_model=SuccessResponse, summary="Отписаться от пользователя")
async def unfollow_user(user_id: int, current_user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    query = select(User).options(selectinload(User.following)).where(User.id == current_user.id)
    curr_user_result = await db.execute(query)
    curr_user_with_follows = curr_user_result.scalars().first()

    for followed_user in curr_user_with_follows.following:
        if followed_user.id == user_id:
            curr_user_with_follows.following.remove(followed_user)
            await db.commit()
            break
    return SuccessResponse(result=True)
